import os
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from .models import Produto, Pedido, ItemPedido
import mercadopago
from dotenv import load_dotenv

load_dotenv()

# Configurar logger
logger = logging.getLogger(__name__)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

@csrf_exempt
@require_POST
def criar_preferencia_pagamento(request):
    """
    Versão simplificada e testada do Mercado Pago
    """
    try:
        data = json.loads(request.body)
        itens_carrinho = data.get('itens', [])
        dados_entrega = data.get('dados_entrega', {})

        if not itens_carrinho:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)

        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

        # Calcular totais
        subtotal = sum(float(item['preco']) * int(item['quantidade']) for item in itens_carrinho)
        frete = 0 if subtotal > 100 else 15
        total = subtotal + frete

        # Construir items
        items_mp = []
        for item in itens_carrinho:
            items_mp.append({
                "id": str(item['id']),
                "title": item['nome'],
                "quantity": int(item['quantidade']),
                "currency_id": "BRL",
                "unit_price": float(item['preco'])
            })
        
        if frete > 0:
            items_mp.append({
                "id": "frete",
                "title": "Frete",
                "quantity": 1,
                "currency_id": "BRL", 
                "unit_price": float(frete)
            })

        # Criar pedido
        with transaction.atomic():
            pedido = Pedido.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                status='pendente',
                valor_total=total,
                nome_entrega=dados_entrega.get('nome', ''),
                email_entrega=dados_entrega.get('email', ''),
                endereco=dados_entrega.get('endereco', ''),
                numero=dados_entrega.get('numero', 'S/N'),
                bairro=dados_entrega.get('bairro', ''),
                cidade=dados_entrega.get('cidade', ''),
                estado=dados_entrega.get('estado', ''),
                cep=dados_entrega.get('cep', ''),
            )
            
            for item in itens_carrinho:
                produto = Produto.objects.get(id=item['id'])
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco']
                )

        # Configuração mínima do Mercado Pago
        base_url = 'http://127.0.0.1:8000'
        
        preference_data = {
            "items": items_mp,
            "back_urls": {
                "success": f"{base_url}/compra-confirmada/",
                "failure": f"{base_url}/compra-erro/",
                "pending": f"{base_url}/compra-pendente/"
            },
            "external_reference": str(pedido.id),
        }

        result = sdk.preference().create(preference_data)

        if result["status"] in [200, 201]:
            payment = result["response"]
            
            pedido.preference_id = payment["id"]
            pedido.save()
            
            return JsonResponse({
                'init_point': payment["init_point"],
                'preference_id': payment["id"],
                'pedido_id': pedido.id
            })
        else:
            pedido.status = 'cancelado'
            pedido.save()
            
            return JsonResponse({
                'error': 'Erro no Mercado Pago',
                'detalhes': result.get('response', {})
            }, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)
@csrf_exempt
@require_POST
def finalizar_compra(request):
    """
    View para finalizar a compra (agora apenas cria pedido, estoque é atualizado via webhook)
    """
    try:
        data = json.loads(request.body)
        itens = data.get('itens', [])
        dados_entrega = data.get('dados_entrega', {})
        
        logger.info(f"Finalizando compra com {len(itens)} itens")

        if not itens:
            return JsonResponse({
                'success': False,
                'message': 'Carrinho vazio'
            }, status=400)
        
        # Verificar estoque primeiro
        for item in itens:
            try:
                produto = Produto.objects.get(id=item['id'])
                quantidade = int(item['quantidade'])
                
                if not produto.estoque_disponivel(quantidade):
                    return JsonResponse({
                        'success': False,
                        'message': f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}'
                    }, status=400)
                    
            except Produto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Produto com ID {item["id"]} não encontrado'
                }, status=404)
        
        # Criar pedido (estoque será atualizado apenas após confirmação do pagamento)
        with transaction.atomic():
            subtotal = sum(float(item['preco']) * int(item['quantidade']) for item in itens)
            frete = 0 if subtotal > settings.FRETE_GRATIS_ACIMA_DE else settings.VALOR_FRETE
            total = subtotal + frete
            
            pedido = Pedido.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                status='pendente',
                valor_total=total,
                # Dados de entrega
                nome_entrega=dados_entrega.get('nome', ''),
                email_entrega=dados_entrega.get('email', ''),
                telefone_entrega=dados_entrega.get('telefone', ''),
                endereco=dados_entrega.get('endereco', ''),
                numero=dados_entrega.get('numero', 'S/N'),
                complemento=dados_entrega.get('complemento', ''),
                bairro=dados_entrega.get('bairro', ''),
                cidade=dados_entrega.get('cidade', ''),
                estado=dados_entrega.get('estado', ''),
                cep=dados_entrega.get('cep', ''),
                dados_entrega=dados_entrega
            )
            
            # Criar itens do pedido (sem atualizar estoque ainda)
            for item in itens:
                produto = Produto.objects.get(id=item['id'])
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=int(item['quantidade']),
                    preco_unitario=float(item['preco'])
                )
        
        logger.info(f"Pedido {pedido.id} criado com sucesso")
        
        return JsonResponse({
            'success': True,
            'message': 'Pedido criado com sucesso. Aguardando pagamento.',
            'pedido_id': pedido.id
        })
        
    except Exception as e:
        logger.error(f"Erro ao finalizar compra: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar compra: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def verificar_estoque(request):
    """
    Verifica estoque em tempo real
    """
    try:
        data = json.loads(request.body)
        produto_id = data.get('produto_id')
        quantidade = int(data.get('quantidade', 1))
        
        produto = get_object_or_404(Produto, id=produto_id)
        disponivel = produto.estoque_disponivel(quantidade)
        
        return JsonResponse({
            'disponivel': disponivel,
            'estoque_atual': produto.estoque,
            'pode_adicionar': produto.estoque > 0,
            'produto_nome': produto.nome,
            'quantidade_solicitada': quantidade
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar estoque: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def atualizar_estoque_carrinho(request):
    """
    Verifica estoque para todos os itens do carrinho
    """
    try:
        data = json.loads(request.body)
        itens = data.get('itens', [])
        
        resultados = []
        carrinho_valido = True
        mensagem_erro = ''
        
        for item in itens:
            produto = get_object_or_404(Produto, id=item['id'])
            quantidade = int(item['quantidade'])
            
            disponivel = produto.estoque_disponivel(quantidade)
            if not disponivel:
                carrinho_valido = False
                mensagem_erro = f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}'
            
            resultados.append({
                'produto_id': produto.id,
                'disponivel': disponivel,
                'estoque_atual': produto.estoque,
                'solicitado': quantidade,
                'produto_nome': produto.nome
            })
        
        return JsonResponse({
            'valido': carrinho_valido,
            'resultados': resultados,
            'mensagem': mensagem_erro if not carrinho_valido else 'Estoque disponível'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar estoque carrinho: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    """
    Webhook para receber notificações do Mercado Pago
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Webhook Mercado Pago recebido: {data}")
        
        # Mercado Pago envia notificações com type e data
        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if payment_id:
                sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info["status"] == 200:
                    payment = payment_info["response"]
                    
                    # Buscar pedido pelo external_reference ou metadata
                    pedido_id = payment.get('external_reference')
                    if not pedido_id:
                        # Tentar buscar pelo metadata
                        metadata = payment.get('metadata', {})
                        pedido_id = metadata.get('pedido_id')
                    
                    if pedido_id:
                        try:
                            pedido = Pedido.objects.get(id=pedido_id)
                            
                            # Atualizar ID do Mercado Pago se necessário
                            if not pedido.id_mercado_pago:
                                pedido.id_mercado_pago = payment_id
                            
                            # Processar status do pagamento
                            status_pagamento = payment.get('status')
                            
                            if status_pagamento == 'approved':
                                # Pagamento aprovado - atualizar estoque
                                pedido.status = 'pago'
                                pedido.save()
                                
                                # Atualizar estoque dos produtos
                                for item in pedido.itens.all():
                                    if item.produto.estoque_disponivel(item.quantidade):
                                        item.produto.reservar_estoque(item.quantidade)
                                    else:
                                        # Se não tiver estoque, cancelar pedido
                                        pedido.status = 'cancelado'
                                        pedido.save()
                                        logger.error(f"Estoque insuficiente para pedido {pedido.id}")
                                        break
                                
                                logger.info(f"Pagamento aprovado para pedido {pedido.id}")
                                
                            elif status_pagamento in ['pending', 'in_process']:
                                pedido.status = 'processando'
                                pedido.save()
                                logger.info(f"Pagamento pendente para pedido {pedido.id}")
                                
                            elif status_pagamento in ['cancelled', 'rejected']:
                                pedido.status = 'cancelado'
                                pedido.save()
                                logger.info(f"Pagamento cancelado para pedido {pedido.id}")
                                
                            else:
                                logger.warning(f"Status de pagamento não tratado: {status_pagamento} para pedido {pedido.id}")
                            
                        except Pedido.DoesNotExist:
                            logger.error(f"Pedido {pedido_id} não encontrado para webhook")
        
        return JsonResponse({'status': 'processed'})
    
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def index(request):
    """
    Página inicial da loja
    """
    try:
        termo_busca = request.GET.get('search', '').strip()
        
        if termo_busca:
            produtos = Produto.objects.filter(
                Q(nome__icontains=termo_busca) | Q(descricao__icontains=termo_busca),
                disponivel=True
            ).order_by('-data_criacao')
        else:
            produtos = Produto.objects.filter(disponivel=True).order_by('-data_criacao')
        
        context = {
            'produtos': produtos,
            'termo_busca': termo_busca
        }
        return render(request, 'index.html', context)
        
    except Exception as e:
        logger.error(f"Erro na página inicial: {str(e)}")
        return render(request, 'index.html', {'produtos': [], 'termo_busca': ''})


def compra_confirmada(request):
    """
    Página de confirmação de compra
    """
    try:
        payment_id = request.GET.get('payment_id')
        pedido_id = request.GET.get('pedido_id')
        status = request.GET.get('status', 'approved')
        
        # Tentar buscar o pedido
        pedido = None
        if pedido_id:
            try:
                pedido = Pedido.objects.get(id=pedido_id)
            except Pedido.DoesNotExist:
                pass
        
        context = {
            'pedido_id': pedido.id if pedido else pedido_id,
            'payment_id': payment_id,
            'status': status,
            'pedido': pedido
        }
        return render(request, 'compra_confirmada.html', context)
        
    except Exception as e:
        logger.error(f"Erro na página de confirmação: {str(e)}")
        return render(request, 'compra_confirmada.html', {})


def compra_erro(request):
    """Página de erro na compra"""
    return render(request, 'compra_erro.html')


def compra_pendente(request):
    """Página de compra pendente"""
    return render(request, 'compra_pendente.html')


def produto_detalhe(request, id):
    """
    Página de detalhes do produto
    """
    try:
        produto = get_object_or_404(Produto, id=id, disponivel=True)
        return render(request, 'produto.html', {'produto': produto})
    except Exception as e:
        logger.error(f"Erro na página do produto {id}: {str(e)}")
        return redirect('index')


def checkout(request):
    """Página de checkout"""
    return render(request, 'checkout.html')


@login_required
def meus_pedidos(request):
    """
    Histórico de pedidos do usuário
    """
    try:
        pedidos = Pedido.objects.filter(usuario=request.user).order_by('-criado_em')
        return render(request, 'meus_pedidos.html', {'pedidos': pedidos})
    except Exception as e:
        logger.error(f"Erro ao carregar pedidos do usuário {request.user.id}: {str(e)}")
        return render(request, 'meus_pedidos.html', {'pedidos': []})


@login_required
def detalhe_pedido(request, pedido_id):
    """
    Detalhes de um pedido específico
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        return render(request, 'detalhe_pedido.html', {'pedido': pedido})
    except Exception as e:
        logger.error(f"Erro ao carregar pedido {pedido_id}: {str(e)}")
        return redirect('meus_pedidos')


@require_GET
def buscar_sugestoes(request):
    """
    Busca produtos para autocomplete
    """
    try:
        termo = request.GET.get('q', '').strip()
        
        if len(termo) < 2:
            return JsonResponse({'sugestoes': []})
        
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo) | Q(descricao__icontains=termo),
            disponivel=True,
            estoque__gt=0
        )[:8]
        
        sugestoes = []
        for produto in produtos:
            sugestoes.append({
                'id': produto.id,
                'nome': produto.nome,
                'preco': str(produto.preco),
                'imagem': produto.imagem.url if produto.imagem else '',
                'estoque': produto.estoque,
                'tem_desconto': produto.tem_desconto(),
                'preco_original': str(produto.preco_original) if produto.preco_original else None
            })
        
        return JsonResponse({'sugestoes': sugestoes})
    
    except Exception as e:
        logger.error(f"Erro na busca de sugestões: {str(e)}")
        return JsonResponse({'sugestoes': [], 'error': str(e)})


@require_GET
@login_required
def obter_status_pedido(request, pedido_id):
    """
    API para obter status do pedido
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        return JsonResponse({
            'pedido_id': pedido.id,
            'status': pedido.status,
            'status_display': pedido.get_status_display(),
            'valor_total': str(pedido.valor_total),
            'criado_em': pedido.criado_em.isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao obter status do pedido {pedido_id}: {str(e)}")
        return JsonResponse({'error': 'Pedido não encontrado'}, status=404)


@csrf_exempt
@require_POST
@login_required
def cancelar_pedido_api(request, pedido_id):
    """
    API para cancelar pedido
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        
        if pedido.cancelar_pedido():
            return JsonResponse({
                'success': True,
                'message': 'Pedido cancelado com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Não foi possível cancelar o pedido neste status'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Erro ao cancelar pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao cancelar pedido: {str(e)}'
        }, status=500)