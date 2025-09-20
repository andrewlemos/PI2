# views.py - Adicione estas views
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from .models import Produto, Pedido, ItemPedido
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q


@csrf_exempt
@require_POST
def finalizar_compra(request):
    """
    View para finalizar a compra e atualizar o estoque
    """
    try:
        data = json.loads(request.body)
        itens = data.get('itens', [])
        
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
                
                if produto.estoque < quantidade:
                    return JsonResponse({
                        'success': False,
                        'message': f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}'
                    }, status=400)
                    
            except Produto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Produto com ID {item["id"]} não encontrado'
                }, status=404)
        
        # Criar pedido
        pedido = Pedido.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            status='pendente'
        )
        
        total_pedido = 0
        
        # Processar itens e atualizar estoque
        for item in itens:
            produto = Produto.objects.get(id=item['id'])
            quantidade = int(item['quantidade'])
            preco_unitario = float(item['preco'])
            
            # Criar item do pedido
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco_unitario
            )
            
            # Atualizar estoque
            produto.estoque -= quantidade
            produto.save()
            
            total_pedido += preco_unitario * quantidade
        
        # Atualizar total do pedido
        pedido.valor_total = total_pedido
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Compra processada com sucesso',
            'pedido_id': pedido.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar compra: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def verificar_estoque(request):
    """
    Verifica estoque em tempo real antes de adicionar ao carrinho
    """
    try:
        data = json.loads(request.body)
        produto_id = data.get('produto_id')
        quantidade = int(data.get('quantidade', 1))
        
        produto = get_object_or_404(Produto, id=produto_id)
        
        return JsonResponse({
            'disponivel': produto.estoque >= quantidade,
            'estoque_atual': produto.estoque,
            'pode_adicionar': produto.estoque > 0,
            'produto_nome': produto.nome
        })
        
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
    except Exception as e:
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
            
            disponivel = produto.estoque >= quantidade
            if not disponivel:
                carrinho_valido = False
                mensagem_erro = f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}'
            
            resultados.append({
                'produto_id': produto.id,
                'disponivel': disponivel,
                'estoque_atual': produto.estoque,
                'solicitado': quantidade
            })
        
        return JsonResponse({
            'valido': carrinho_valido,
            'resultados': resultados,
            'mensagem': mensagem_erro if not carrinho_valido else 'Estoque disponível'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def index(request):
    """
    Página inicial da loja (lista de produtos)
    """
    produtos = Produto.objects.all()
    return render(request, 'index.html', {'produtos': produtos})

def compra_confirmada(request):
    """
    Página de confirmação de compra
    """
    pedido_id = request.GET.get('pedido_id')
    context = {'pedido_id': pedido_id}
    return render(request, 'compra_confirmada.html', context)

def produto_detalhe(request, id):
    """
    Mostra a página de detalhes de um produto específico
    """
    produto = get_object_or_404(Produto, id=id)
    # Corrigido para usar o template existente
    return render(request, 'produto.html', {'produto': produto})

def checkout(request):
    # Renderiza o template de checkout
    return render(request, 'checkout.html')

@login_required
def meus_pedidos(request):
    """
    Página com histórico de pedidos do usuário
    """
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'meus_pedidos.html', {'pedidos': pedidos})


@login_required
def detalhe_pedido(request, pedido_id):
    """
    Detalhes de um pedido específico
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'detalhe_pedido.html', {'pedido': pedido})


@require_GET
def buscar_sugestoes(request):
    """
    Busca produtos para autocomplete na barra de pesquisa
    """
    termo = request.GET.get('q', '').strip()
    
    if len(termo) < 2:
        return JsonResponse({'sugestoes': []})
    
    try:
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo) | Q(descricao__icontains=termo),
            disponivel=True,
            estoque__gt=0
        )[:5]
        
        sugestoes = []
        for produto in produtos:
            sugestoes.append({
                'id': produto.id,
                'nome': produto.nome,
                'preco': str(produto.preco),
                'imagem': produto.imagem.url if produto.imagem else '',
                'estoque': produto.estoque
            })
        
        return JsonResponse({'sugestoes': sugestoes})
    
    except Exception as e:
        return JsonResponse({'sugestoes': [], 'error': str(e)})
