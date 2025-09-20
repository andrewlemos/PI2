from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.utils.html import escape
from .models import Produto
import json

def index(request):
    # Obter termo de busca se existir
    termo_busca = request.GET.get('search', '').strip()
    
    if termo_busca:
        # Filtrar produtos que contenham o termo no nome ou descrição
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo_busca) | 
            Q(descricao__icontains=termo_busca),
            disponivel=True  # Só mostrar produtos disponíveis
        )
    else:
        # Mostrar todos os produtos disponíveis se não houver busca
        produtos = Produto.objects.filter(disponivel=True)
    
    return render(request, 'index.html', {
        'produtos': produtos,
        'termo_busca': termo_busca
    })

def produto_detalhe(request, id):
    produto = get_object_or_404(Produto, id=id, disponivel=True)
    return render(request, 'produto.html', {'produto': produto})

def checkout(request):
    return render(request, 'checkout.html')

@csrf_exempt
def criar_preferencia_pagamento(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Aqui você processaria os itens do carrinho e criaria a preferência real
            # Esta é uma versão simulada para desenvolvimento
            return JsonResponse({
                'id': 'simulado-123456789',
                'init_point': 'https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=simulado-123456789'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# ✅ Função para a busca de sugestões CORRIGIDA
@require_GET
def buscar_sugestoes(request):
    termo = request.GET.get('q', '')
    
    if len(termo) < 2:
        return JsonResponse({'sugestoes': []})
    
    produtos = Produto.objects.filter(
        Q(nome__icontains=termo) | Q(descricao__icontains=termo),
        disponivel=True
    )[:5]
    
    sugestoes = []
    for produto in produtos:
        sugestoes.append({
            'id': produto.id,
            'nome': produto.nome,
            'preco': str(produto.preco),
            'imagem': produto.imagem.url if produto.imagem else ''
        })
    
    return JsonResponse({'sugestoes': sugestoes})