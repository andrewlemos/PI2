import os
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from .models import Produto, Pedido, ItemPedido, Cupom, CupomUso
import mercadopago
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ===============================
# CONFIGURAÇÃO MERCADO PAGO
# ===============================
def get_mp_access_token():
    token = os.getenv("MP_ACCESS_TOKEN")
    if not token:
        logger.error("MP_ACCESS_TOKEN não encontrado")
    return token

def get_mp_sdk():
    token = get_mp_access_token()
    if not token:
        raise ValueError("Access Token do Mercado Pago não configurado")
    return mercadopago.SDK(token)

# ===============================
# ATALHOS DE LOGIN/LOGOUT
# ===============================
def login_redirect(request):
    return redirect('account_login')

def logout_redirect(request):
    auth_logout(request)
    return redirect('index')

# ===============================
# VALIDAÇÕES
# ===============================
def validar_dados_entrega(dados_entrega):
    campos_obrigatorios = ['nome', 'email', 'cep', 'endereco', 'bairro', 'cidade', 'estado']
    faltando = [c for c in campos_obrigatorios if not dados_entrega.get(c, '').strip()]
    return faltando

def validar_itens_carrinho(itens_carrinho):
    if not itens_carrinho:
        return {'error': 'Carrinho vazio'}
    for item in itens_carrinho:
        try:
            produto_id = item.get('id')
            quantidade = int(item.get('quantidade', 1))
            preco = float(item.get('preco', 0))
            if not produto_id or quantidade <= 0 or preco <= 0:
                return {'error': 'Dados inválidos no item'}
            produto = Produto.objects.get(id=produto_id)
            if not produto.estoque_disponivel(quantidade):
                return {'error': f'Estoque insuficiente para {produto.nome}'}
        except Produto.DoesNotExist:
            return {'error': f'Produto não encontrado: {produto_id}'}
        except Exception as e:
            return {'error': str(e)}
    return {'success': True}

# ===============================
# API: APLICAR CUPOM (CORRIGIDA - VALIDAÇÃO COMPLETA)
# ===============================
@csrf_exempt
@require_POST
def aplicar_cupom(request):
    try:
        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()
        itens = data.get('itens', [])

        if not codigo:
            return JsonResponse({'success': False, 'error': 'Digite o código do cupom.'}, status=400)
        if not itens:
            return JsonResponse({'success': False, 'error': 'Adicione itens ao carrinho primeiro.'}, status=400)

        # Buscar cupom
        try:
            cupom = Cupom.objects.get(codigo=codigo, ativo=True)
        except Cupom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cupom inválido ou inativo.'}, status=404)

        # CORREÇÃO: Garantir que ambas as datas sejam do mesmo tipo
        agora = timezone.now().date()

        # Converter datas do cupom para date se necessário
        data_inicio_cupom = cupom.data_inicio.date() if hasattr(cupom.data_inicio, 'date') else cupom.data_inicio
        data_fim_cupom = cupom.data_fim.date() if cupom.data_fim and hasattr(cupom.data_fim, 'date') else cupom.data_fim

        if cupom.data_inicio and agora < data_inicio_cupom:
            return JsonResponse({'success': False, 'error': 'Cupom ainda não está válido.'}, status=400)
        if cupom.data_fim and agora > data_fim_cupom:
            return JsonResponse({'success': False, 'error': 'Cupom expirado.'}, status=400)

        # CORREÇÃO: Verificar limite de uso geral
        if cupom.limite_uso:
            usos_totais = cupom.usos.count()
            if usos_totais >= cupom.limite_uso:
                return JsonResponse({'success': False, 'error': 'Limite de usos do cupom esgotado.'}, status=400)

        # CORREÇÃO: Verificar limite por usuário
        if cupom.limite_por_usuario and request.user.is_authenticated:
            usos_usuario = cupom.usos.filter(pedido__usuario=request.user).count()
            if usos_usuario >= cupom.limite_por_usuario:
                return JsonResponse({'success': False, 'error': 'Você já usou este cupom o número máximo de vezes permitido.'}, status=400)

        # CORREÇÃO: Converter tudo para float antes dos cálculos
        subtotal = sum(float(i.get('preco', 0)) * int(i.get('quantidade', 1)) for i in itens)
        valor_cupom = float(cupom.valor)  # Converter Decimal para float
        
        if cupom.tipo == 'percentual':
            desconto = subtotal * (valor_cupom / 100)
        else:
            desconto = min(valor_cupom, subtotal)

        return JsonResponse({
            'success': True,
            'desconto': round(desconto, 2),
            'cupom': {
                'codigo': cupom.codigo,
                'tipo': cupom.get_tipo_display(),
                'valor': valor_cupom  # Já convertido para float
            }
        })

    except Exception as e:
        logger.error(f"Erro ao aplicar cupom: {e}")
        return JsonResponse({'success': False, 'error': 'Erro ao validar cupom.'}, status=500)

# ===============================
# API: CRIAR PREFERÊNCIA (CUPOM SINCRONIZADO COM REGISTRO DE USO)
# ===============================
@csrf_exempt
@require_POST
def criar_preferencia_pagamento(request):
    try:
        logger.info("=== INICIANDO CRIAÇÃO DE PREFERÊNCIA ===")
        if not request.body:
            return JsonResponse({'error': 'Body vazio'}, status=400)

        data = json.loads(request.body)
        itens_carrinho = data.get('itens', [])
        dados_entrega = data.get('dados_entrega', {})

        if not itens_carrinho:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)

        campos_faltando = validar_dados_entrega(dados_entrega)
        if campos_faltando:
            return JsonResponse({'error': f'Campos faltando: {", ".join(campos_faltando)}'}, status=400)

        validacao = validar_itens_carrinho(itens_carrinho)
        if 'error' in validacao:
            return JsonResponse({'error': validacao['error']}, status=400)

        # CÁLCULO COM CUPOM
        subtotal = sum(float(i['preco']) * int(i['quantidade']) for i in itens_carrinho)
        frete = 0 if subtotal >= getattr(settings, 'FRETE_GRATIS_ACIMA_DE', 100) else getattr(settings, 'VALOR_FRETE', 15)

        cupom_codigo = dados_entrega.get('cupom', '').strip().upper()
        cupom = None
        desconto_cupom = 0

        if cupom_codigo:
            try:
                cupom = Cupom.objects.get(codigo=cupom_codigo, ativo=True)
                # CORREÇÃO: Garantir que ambas as datas sejam do mesmo tipo
                agora = timezone.now().date()

                # Converter datas do cupom para date se necessário
                data_inicio_cupom = cupom.data_inicio.date() if hasattr(cupom.data_inicio, 'date') else cupom.data_inicio
                data_fim_cupom = cupom.data_fim.date() if cupom.data_fim and hasattr(cupom.data_fim, 'date') else cupom.data_fim

                if (cupom.data_inicio and agora < data_inicio_cupom) or (cupom.data_fim and agora > data_fim_cupom):
                    cupom = None
                elif cupom.limite_uso and cupom.usos.count() >= cupom.limite_uso:
                    cupom = None
                elif cupom.limite_por_usuario and request.user.is_authenticated:
                    usos = cupom.usos.filter(pedido__usuario=request.user).count()
                    if usos >= cupom.limite_por_usuario:
                        cupom = None
                if cupom:
                    # CORREÇÃO: Converter Decimal para float
                    valor_cupom_float = float(cupom.valor)
                    if cupom.tipo == 'percentual':
                        desconto_cupom = subtotal * (valor_cupom_float / 100)
                    else:
                        desconto_cupom = min(valor_cupom_float, subtotal)
                    logger.info(f"Cupom {cupom_codigo} aplicado: desconto de R$ {desconto_cupom:.2f}")
            except Cupom.DoesNotExist:
                cupom = None
                logger.warning(f"Cupom {cupom_codigo} não encontrado")

        total = max(subtotal + frete - desconto_cupom, 0)
        
        # LOG PARA DEBUG
        logger.info(f"Subtotal: R$ {subtotal:.2f}, Frete: R$ {frete:.2f}, Desconto: R$ {desconto_cupom:.2f}, Total: R$ {total:.2f}")

        # ITENS PARA MP
        items_mp = []
        for item in itens_carrinho:
            items_mp.append({
                "id": str(item['id']),
                "title": item['nome'][:250],
                "quantity": int(item['quantidade']),
                "currency_id": "BRL",
                "unit_price": float(item['preco'])
            })

        # ADICIONAR FRETE COMO ITEM SEPARADO
        if frete > 0:
            items_mp.append({
                "id": "frete",
                "title": "Taxa de Entrega",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(frete)
            })

        # CORREÇÃO: ADICIONAR DESCONTO DO CUPOM COMO ITEM NEGATIVO
        if desconto_cupom > 0:
            items_mp.append({
                "id": "desconto_cupom",
                "title": f"Desconto - {cupom_codigo}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": -float(desconto_cupom)  # VALOR NEGATIVO
            })
            logger.info(f"Item de desconto adicionado: -R$ {desconto_cupom:.2f}")

        with transaction.atomic():
            pedido = Pedido.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                status='pendente',
                valor_total=total,
                cupom=cupom,
                desconto_cupom=round(desconto_cupom, 2),
                nome_entrega=dados_entrega.get('nome', '').strip(),
                email_entrega=dados_entrega.get('email', '').strip(),
                telefone_entrega=dados_entrega.get('telefone', '').strip(),
                endereco=dados_entrega.get('endereco', '').strip(),
                numero=dados_entrega.get('numero', '').strip() or 'S/N',
                complemento=dados_entrega.get('complemento', '').strip(),
                bairro=dados_entrega.get('bairro', '').strip(),
                cidade=dados_entrega.get('cidade', '').strip(),
                estado=dados_entrega.get('estado', '').strip(),
                cep=dados_entrega.get('cep', '').strip(),
                dados_entrega=json.dumps(dados_entrega, ensure_ascii=False)
            )

            for item in itens_carrinho:
                produto = Produto.objects.get(id=item['id'])
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=int(item['quantidade']),
                    preco_unitario=float(item['preco'])
                )

            # CORREÇÃO: REGISTRAR USO DO CUPOM IMEDIATAMENTE AO CRIAR O PEDIDO
            if cupom:
                # Verificar se já existe um uso para evitar duplicação
                if not CupomUso.objects.filter(cupom=cupom, pedido=pedido).exists():
                    CupomUso.objects.create(cupom=cupom, pedido=pedido)
                    logger.info(f"Cupom {cupom_codigo} registrado para o pedido {pedido.id}")

        base_url = request.build_absolute_uri('/').rstrip('/')
        preference_data = {
            "items": items_mp,
            "back_urls": {
                "success": f"{base_url}/compra-confirmada/?pedido_id={pedido.id}",
                "failure": f"{base_url}/compra-erro/",
                "pending": f"{base_url}/compra-pendente/"
            },
            "external_reference": str(pedido.id),
            "statement_descriptor": "MINHA LOJA",
            "binary_mode": True
        }

        sdk = get_mp_sdk()
        result = sdk.preference().create(preference_data)

        if result["status"] in [200, 201]:
            payment = result["response"]
            pedido.preference_id = payment["id"]
            pedido.save()

            # LOG FINAL
            logger.info(f"Preferência criada com sucesso. Total: R$ {total:.2f}, Desconto: R$ {desconto_cupom:.2f}")

            return JsonResponse({
                'success': True,
                'init_point': payment["init_point"],
                'preference_id': payment["id"],
                'pedido_id': pedido.id
            })
        else:
            pedido.status = 'cancelado'
            pedido.save()
            # CORREÇÃO: Se falhar, remover o uso do cupom
            if cupom:
                CupomUso.objects.filter(cupom=cupom, pedido=pedido).delete()
                logger.info(f"Uso do cupom {cupom_codigo} removido devido a erro no Mercado Pago")
            return JsonResponse({'error': 'Erro no Mercado Pago'}, status=400)

    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        return JsonResponse({'error': 'Erro interno'}, status=500)

# ===============================
# WEBHOOK: REGISTRA USO DO CUPOM (CORRIGIDO)
# ===============================
@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    try:
        data = json.loads(request.body)
        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if not payment_id:
                return JsonResponse({'status': 'ignored'})

            sdk = get_mp_sdk()
            payment_info = sdk.payment().get(payment_id)
            if payment_info["status"] != 200:
                return JsonResponse({'status': 'error'})

            payment = payment_info["response"]
            pedido_id = payment.get('external_reference')
            status = payment.get('status')

            if pedido_id:
                try:
                    pedido = Pedido.objects.get(id=pedido_id)
                    if status == 'approved':
                        pedido.status = 'pago'
                        for item in pedido.itens.all():
                            item.produto.reservar_estoque(item.quantidade)
                        # CORREÇÃO: Verificar se o uso do cupom já foi registrado
                        if pedido.cupom and not CupomUso.objects.filter(cupom=pedido.cupom, pedido=pedido).exists():
                            CupomUso.objects.create(cupom=pedido.cupom, pedido=pedido)
                            logger.info(f"Cupom {pedido.cupom.codigo} registrado via webhook para pedido {pedido.id}")
                    elif status in ['cancelled', 'rejected']:
                        pedido.status = 'cancelado'
                        # CORREÇÃO: Remover uso do cupom se o pagamento falhar
                        if pedido.cupom:
                            CupomUso.objects.filter(cupom=pedido.cupom, pedido=pedido).delete()
                            logger.info(f"Uso do cupom {pedido.cupom.codigo} removido devido a cancelamento do pedido {pedido.id}")
                    pedido.save()
                except Pedido.DoesNotExist:
                    logger.warning(f"Pedido {pedido_id} não encontrado no webhook")
        return JsonResponse({'status': 'processed'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===============================
# VIEWS DE REDIRECIONAMENTO
# ===============================
def compra_confirmada(request):
    pedido_id = request.GET.get('pedido_id')
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status', 'approved')
    
    pedido = None
    if pedido_id:
        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido and payment_id:
            pedido = Pedido.objects.filter(payment_id=payment_id).first()
    
    if not pedido:
        return render(request, 'compra_confirmada.html', {
            'pedido': None,
            'message': 'Compra processada com sucesso! Em breve você receberá a confirmação.'
        })
    
    return render(request, 'compra_confirmada.html', {
        'pedido': pedido,
        'payment_id': payment_id,
        'status': status
    })

def compra_erro(request):
    pedido_id = request.GET.get('pedido_id')
    pedido = Pedido.objects.filter(id=pedido_id).first() if pedido_id else None
    
    return render(request, 'compra_erro.html', {
        'pedido': pedido,
        'error_message': request.GET.get('message', 'Ocorreu um erro durante o pagamento.')
    })

def compra_pendente(request):
    pedido_id = request.GET.get('pedido_id')
    pedido = Pedido.objects.filter(id=pedido_id).first() if pedido_id else None
    
    return render(request, 'compra_pendente.html', {
        'pedido': pedido,
        'message': 'Seu pagamento está sendo processado. Você receberá uma confirmação em breve.'
    })

# ===============================
# VIEWS PRINCIPAIS
# ===============================
def index(request):
    termo = request.GET.get('search', '').strip()
    if termo:
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo) | Q(descricao__icontains=termo),
            disponivel=True
        ).order_by('-data_criacao')
    else:
        produtos = Produto.objects.filter(disponivel=True).order_by('-data_criacao')
    
    return render(request, 'index.html', {
        'produtos': produtos, 
        'termo_busca': termo
    })

def produto_detalhe(request, id):
    produto = get_object_or_404(Produto, id=id, disponivel=True)
    return render(request, 'produto.html', {'produto': produto})

def checkout(request):
    return render(request, 'checkout.html')

@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'meus_pedidos.html', {'pedidos': pedidos})

@login_required
def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'detalhe_pedido.html', {'pedido': pedido})

# ===============================
# APIs AUXILIARES
# ===============================
@require_GET
def buscar_sugestoes(request):
    termo = request.GET.get('q', '').strip()
    if len(termo) < 2:
        return JsonResponse({'sugestoes': []})

    produtos = Produto.objects.filter(
        Q(nome__icontains=termo) | Q(descricao__icontains=termo),
        disponivel=True,
        estoque__gt=0
    )[:8]

    sugestoes = [{
        'id': p.id,
        'nome': p.nome,
        'preco': str(p.preco),
        'imagem': p.imagem.url if p.imagem else '',
        'estoque': p.estoque,
        'tem_desconto': p.tem_desconto(),
        'preco_original': str(p.preco_original) if p.preco_original else None
    } for p in produtos]

    return JsonResponse({'sugestoes': sugestoes})

@require_GET
@login_required
def obter_status_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return JsonResponse({
        'pedido_id': pedido.id,
        'status': pedido.status,
        'status_display': pedido.get_status_display(),
        'valor_total': str(pedido.valor_total),
        'criado_em': pedido.criado_em.isoformat()
    })

@csrf_exempt
@require_POST
@login_required
def cancelar_pedido_api(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    if pedido.cancelar_pedido():
        # CORREÇÃO: Remover uso do cupom ao cancelar pedido
        if pedido.cupom:
            CupomUso.objects.filter(cupom=pedido.cupom, pedido=pedido).delete()
            logger.info(f"Uso do cupom {pedido.cupom.codigo} removido devido a cancelamento manual do pedido {pedido.id}")
        return JsonResponse({'success': True, 'message': 'Pedido cancelado'})
    return JsonResponse({'success': False, 'message': 'Não pode ser cancelado'}, status=400)

# ===============================
# APIs DE ESTOQUE
# ===============================
@csrf_exempt
@require_POST
def verificar_estoque(request):
    try:
        data = json.loads(request.body)
        produto_id = data.get('produto_id')
        quantidade = int(data.get('quantidade', 1))
        
        if not produto_id:
            return JsonResponse({'error': 'ID do produto não informado'}, status=400)
        
        produto = get_object_or_404(Produto, id=produto_id)
        disponivel = produto.estoque_disponivel(quantidade)
        
        return JsonResponse({
            'disponivel': disponivel,
            'estoque_atual': produto.estoque,
            'pode_adicionar': produto.estoque > 0,
            'produto_nome': produto.nome
        })
        
    except ValueError:
        return JsonResponse({'error': 'Quantidade inválida'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao verificar estoque: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def atualizar_estoque_carrinho(request):
    try:
        data = json.loads(request.body)
        itens = data.get('itens', [])
        resultados = []
        valido = True
        
        for item in itens:
            produto_id = item.get('id')
            quantidade = int(item.get('quantidade', 1))
            
            if not produto_id:
                continue
                
            try:
                produto = Produto.objects.get(id=produto_id)
                disponivel = produto.estoque_disponivel(quantidade)
                
                if not disponivel:
                    valido = False
                    
                resultados.append({
                    'produto_id': produto.id,
                    'disponivel': disponivel,
                    'estoque_atual': produto.estoque,
                    'solicitado': quantidade,
                    'produto_nome': produto.nome
                })
                
            except Produto.DoesNotExist:
                resultados.append({
                    'produto_id': produto_id,
                    'disponivel': False,
                    'estoque_atual': 0,
                    'solicitado': quantidade,
                    'produto_nome': 'Produto não encontrado'
                })
                valido = False
        
        return JsonResponse({
            'valido': valido, 
            'resultados': resultados,
            'mensagem': 'Estoque verificado com sucesso' if valido else 'Estoque insuficiente para alguns produtos'
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar estoque do carrinho: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)