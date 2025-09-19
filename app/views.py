from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Produto
import json

def index(request):
    produtos = Produto.objects.all()
    return render(request, 'index.html', {'produtos': produtos})

def produto_detalhe(request, id):
    produto = get_object_or_404(Produto, id=id)
    return render(request, 'produto.html', {'produto': produto})

def checkout(request):
    return render(request, 'checkout.html')

@csrf_exempt
def criar_preferencia_pagamento(request):
    if request.method == 'POST':
        try:
            # Simulação da integração com Mercado Pago
            # Em produção, substituir pela integração real
            data = json.loads(request.body)
            
            # Retornar um ID simulado para desenvolvimento
            return JsonResponse({
                'id': 'simulado-123456789',
                'init_point': 'https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=simulado-123456789'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)