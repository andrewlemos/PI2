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
from .models import Produto, Pedido, ItemPedido
import mercadopago
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ===============================
# CONFIGURAÇÃO MERCADO PAGO
# ===============================
def get_mp_access_token():
    """Obtém o access token do Mercado Pago com fallback"""
    token = os.getenv("MP_ACCESS_TOKEN")
    if not token:
        logger.error("MP_ACCESS_TOKEN não encontrado nas variáveis de ambiente")
    return token

def get_mp_sdk():
    """Inicializa e retorna a SDK do Mercado Pago"""
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
    """Valida os dados de entrega obrigatórios"""
    campos_obrigatorios = ['nome', 'email', 'cep', 'endereco', 'bairro', 'cidade', 'estado']
    campos_faltando = []
    
    for campo in campos_obrigatorios:
        valor = dados_entrega.get(campo, '').strip()
        if not valor:
            campos_faltando.append(campo)
    
    return campos_faltando

def validar_itens_carrinho(itens_carrinho):
    """Valida os itens do carrinho e verifica estoque"""
    if not itens_carrinho:
        return {'error': 'Carrinho vazio'}
    
    for item in itens_carrinho:
        try:
            produto_id = item.get('id')
            quantidade = int(item.get('quantidade', 1))
            preco = float(item.get('preco', 0))
            
            if not produto_id:
                return {'error': 'ID do produto não informado'}
            
            if quantidade <= 0:
                return {'error': f'Quantidade inválida para produto {produto_id}'}
            
            if preco <= 0:
                return {'error': f'Preço inválido para produto {produto_id}'}
            
            # Verificar se produto existe e tem estoque
            produto = Produto.objects.get(id=produto_id)
            if not produto.estoque_disponivel(quantidade):
                return {
                    'error': f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}'
                }
                
        except Produto.DoesNotExist:
            return {'error': f'Produto não encontrado: {produto_id}'}
        except ValueError as e:
            return {'error': f'Dados inválidos no item: {str(e)}'}
        except Exception as e:
            return {'error': f'Erro ao validar item: {str(e)}'}
    
    return {'success': True}

# ===============================
# API: CRIAR PREFERÊNCIA MERCADO PAGO - VERSÃO SIMPLIFICADA
# ===============================
@csrf_exempt
@require_POST
def criar_preferencia_pagamento(request):
    """
    Cria uma preferência de pagamento no Mercado Pago - Versão Simplificada
    """
    try:
        logger.info("=== INICIANDO CRIAÇÃO DE PREFERÊNCIA DE PAGAMENTO ===")
        
        # Verificar se o body está vazio
        if not request.body:
            logger.error("Body vazio na requisição")
            return JsonResponse({'error': 'Body vazio'}, status=400)
        
        # Parse do JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        itens_carrinho = data.get('itens', [])
        dados_entrega = data.get('dados_entrega', {})

        logger.info(f"Processando {len(itens_carrinho)} itens do carrinho")

        # Validar dados básicos
        if not itens_carrinho:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)

        # Validar dados de entrega
        campos_faltando = validar_dados_entrega(dados_entrega)
        if campos_faltando:
            return JsonResponse({
                'error': f'Campos obrigatórios faltando: {", ".join(campos_faltando)}'
            }, status=400)

        # Validar itens do carrinho
        validacao_itens = validar_itens_carrinho(itens_carrinho)
        if 'error' in validacao_itens:
            return JsonResponse({'error': validacao_itens['error']}, status=400)

        # Inicializar SDK do Mercado Pago
        try:
            sdk = get_mp_sdk()
        except ValueError as e:
            logger.error(f"Erro na configuração do Mercado Pago: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

        # Calcular totais
        subtotal = 0
        for item in itens_carrinho:
            preco = float(item['preco'])
            quantidade = int(item['quantidade'])
            subtotal += preco * quantidade

        frete_gratis_acima_de = getattr(settings, 'FRETE_GRATIS_ACIMA_DE', 100)
        valor_frete = getattr(settings, 'VALOR_FRETE', 15)
        frete = 0 if subtotal >= frete_gratis_acima_de else valor_frete
        total = subtotal + frete

        logger.info(f"Totais - Subtotal: R$ {subtotal:.2f}, Frete: R$ {frete:.2f}, Total: R$ {total:.2f}")

        # Preparar itens para Mercado Pago
        items_mp = []
        for item in itens_carrinho:
            items_mp.append({
                "id": str(item['id']),
                "title": item['nome'][:250],
                "description": f"Produto: {item['nome']}"[:500],
                "quantity": int(item['quantidade']),
                "currency_id": "BRL",
                "unit_price": float(item['preco'])
            })
        
        # Adicionar frete como item separado se houver
        if frete > 0:
            items_mp.append({
                "id": "frete",
                "title": "Taxa de Entrega",
                "description": "Custo do frete",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(frete)
            })

        # Criar pedido no banco dentro de uma transação
        with transaction.atomic():
            pedido = Pedido.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                status='pendente',
                valor_total=total,
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
            
            # Criar itens do pedido
            for item in itens_carrinho:
                produto = Produto.objects.get(id=item['id'])
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=int(item['quantidade']),
                    preco_unitario=float(item['preco'])
                )

            logger.info(f"Pedido #{pedido.id} criado com sucesso")

        # Configurar URLs de retorno - VERSÃO SIMPLIFICADA
        base_url = 'http://127.0.0.1:8000'
        
        # URLs básicas sem parâmetros (o Mercado Pago é sensível a isso)
        back_urls = {
            "success": f"{base_url}/compra-confirmada/",
            "failure": f"{base_url}/compra-erro/", 
            "pending": f"{base_url}/compra-pendente/"
        }

        # Configuração MÍNIMA da preferência
        preference_data = {
            "items": items_mp,
            "back_urls": back_urls,
            # REMOVIDO: auto_return - causa problemas
            "external_reference": str(pedido.id),
            # REMOVIDO: notification_url temporariamente para simplificar
            "statement_descriptor": "MINHA LOJA",
            "binary_mode": True,
            "expires": False,  # A preferência não expira
        }

        logger.info(f"Enviando preferência para Mercado Pago: {len(items_mp)} itens")
        logger.info(f"Back URLs: {back_urls}")

        # Criar preferência no Mercado Pago
        result = sdk.preference().create(preference_data)

        logger.info(f"Resposta Mercado Pago - Status: {result.get('status')}")

        if result["status"] in [200, 201]:
            payment = result["response"]
            
            # Atualizar pedido com ID da preferência
            pedido.preference_id = payment["id"]
            pedido.save()
            
            # Construir URL de redirecionamento com parâmetros
            init_point = payment["init_point"]
            
            response_data = {
                'success': True,
                'init_point': init_point,
                'preference_id': payment["id"],
                'pedido_id': pedido.id,
                'message': 'Preferência criada com sucesso'
            }
            
            logger.info(f"✅ Preferência {payment['id']} criada com sucesso para pedido #{pedido.id}")
            logger.info(f"🔗 Init Point: {init_point}")
            
            return JsonResponse(response_data)
            
        else:
            # Reverter pedido se falhar no Mercado Pago
            pedido.status = 'cancelado'
            pedido.save()
            
            error_details = result.get('response', {})
            logger.error(f"❌ Erro Mercado Pago - Status: {result['status']}, Detalhes: {error_details}")
            
            error_message = error_details.get('message', 'Erro desconhecido no Mercado Pago')
            
            return JsonResponse({
                'error': f'Erro ao criar pagamento: {error_message}',
                'detalhes': error_details,
                'status_code': result["status"]
            }, status=400)

    except Exception as e:
        logger.error(f"💥 Erro interno na criação de preferência: {str(e)}", exc_info=True)
        
        # Tentar reverter pedido se foi criado
        if 'pedido' in locals() and pedido.id:
            try:
                pedido.status = 'cancelado'
                pedido.save()
                logger.info(f"Pedido #{pedido.id} cancelado devido a erro interno")
            except Exception:
                pass
        
        return JsonResponse({
            'error': f'Erro interno do servidor: {str(e)}'
        }, status=500)

# ===============================
# WEBHOOK MERCADO PAGO (OPCIONAL POR ENQUANTO)
# ===============================
@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    """
    Processa notificações do Mercado Pago - Versão Simplificada
    """
    try:
        data = json.loads(request.body)
        logger.info(f"📩 Webhook recebido - Tipo: {data.get('type')}")

        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if not payment_id:
                return JsonResponse({'status': 'ignored'})

            try:
                sdk = get_mp_sdk()
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info["status"] != 200:
                    return JsonResponse({'status': 'error'})

                payment = payment_info["response"]
                pedido_id = payment.get('external_reference')
                status = payment.get('status')

                logger.info(f"💰 Pagamento {payment_id} - Status: {status}, Pedido: {pedido_id}")

                if pedido_id:
                    try:
                        pedido = Pedido.objects.get(id=pedido_id)
                        
                        if status == 'approved':
                            pedido.status = 'pago'
                            pedido.payment_id = payment_id
                            # Reservar estoque
                            for item in pedido.itens.all():
                                item.produto.reservar_estoque(item.quantidade)
                            logger.info(f"✅ Pedido #{pedido_id} marcado como pago")
                            
                        elif status in ['cancelled', 'rejected']:
                            pedido.status = 'cancelado'
                            pedido.payment_id = payment_id
                            logger.info(f"❌ Pedido #{pedido_id} marcado como cancelado")
                            
                        pedido.save()

                    except Pedido.DoesNotExist:
                        logger.error(f"📦 Pedido {pedido_id} não encontrado")

            except Exception as e:
                logger.error(f"🔧 Erro ao processar pagamento {payment_id}: {str(e)}")

        return JsonResponse({'status': 'processed'})

    except Exception as e:
        logger.error(f"💥 Erro no webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ===============================
# VIEWS DE REDIRECIONAMENTO MELHORADAS
# ===============================
def compra_confirmada(request):
    """
    Página de confirmação de compra - Melhorada
    """
    pedido_id = request.GET.get('pedido_id')
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status', 'approved')
    
    pedido = None
    if pedido_id:
        pedido = Pedido.objects.filter(id=pedido_id).first()
        # Se não encontrou pelo pedido_id, tenta buscar pelo collection_id (Mercado Pago)
        if not pedido and payment_id:
            pedido = Pedido.objects.filter(payment_id=payment_id).first()
    
    # Se ainda não encontrou o pedido, tenta buscar na sessão ou mostrar página genérica
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
    """
    Página de erro na compra
    """
    pedido_id = request.GET.get('pedido_id')
    pedido = Pedido.objects.filter(id=pedido_id).first() if pedido_id else None
    
    return render(request, 'compra_erro.html', {
        'pedido': pedido,
        'error_message': request.GET.get('message', 'Ocorreu um erro durante o pagamento.')
    })

def compra_pendente(request):
    """
    Página de compra pendente
    """
    pedido_id = request.GET.get('pedido_id')
    pedido = Pedido.objects.filter(id=pedido_id).first() if pedido_id else None
    
    return render(request, 'compra_pendente.html', {
        'pedido': pedido,
        'message': 'Seu pagamento está sendo processado. Você receberá uma confirmação em breve.'
    })

# ===============================
# VIEWS PRINCIPAIS (MANTIDAS)
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
# APIs AUXILIARES (MANTIDAS)
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
        return JsonResponse({'success': True, 'message': 'Pedido cancelado'})
    return JsonResponse({'success': False, 'message': 'Não pode ser cancelado'}, status=400)

# ===============================
# APIs DE ESTOQUE (MANTIDAS)
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