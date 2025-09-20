# app/urls.py - CORRIGIDO
from django.urls import path
from . import views
# Remova a importação específica e use views.funcao

urlpatterns = [
    path('', views.index, name='index'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('checkout/', views.checkout, name='checkout'),
    # path('criar-pagamento/', views.criar_preferencia_pagamento, name='criar_pagamento'),
    path('api/buscar-sugestoes/', views.buscar_sugestoes, name='buscar_sugestoes'),
    
    # Novas URLs para controle de estoque
    path('api/finalizar-compra/', views.finalizar_compra, name='finalizar_compra'),
    path('api/verificar-estoque/', views.verificar_estoque, name='verificar_estoque'),
    path('api/atualizar-estoque-carrinho/', views.atualizar_estoque_carrinho, name='atualizar_estoque_carrinho'),
    path('compra-confirmada/', views.compra_confirmada, name='compra_confirmada'),
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
]