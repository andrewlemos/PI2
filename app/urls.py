from django.urls import path
from . import views

urlpatterns = [
    # Páginas principais
    path('', views.index, name='index'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Páginas de status de compra
    path('compra-confirmada/', views.compra_confirmada, name='compra_confirmada'),
    path('compra-erro/', views.compra_erro, name='compra_erro'),
    path('compra-pendente/', views.compra_pendente, name='compra_pendente'),
    
    # Gestão de pedidos
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
    
    # APIs - Pagamento
    path('api/criar-preferencia-pagamento/', views.criar_preferencia_pagamento, name='criar_preferencia_pagamento'),
    path('api/finalizar-compra/', views.finalizar_compra, name='finalizar_compra'),
    
    # APIs - Estoque e Produtos
    path('api/verificar-estoque/', views.verificar_estoque, name='verificar_estoque'),
    path('api/atualizar-estoque-carrinho/', views.atualizar_estoque_carrinho, name='atualizar_estoque_carrinho'),
    path('api/buscar-sugestoes/', views.buscar_sugestoes, name='buscar_sugestoes'),
    
    # Webhooks - IMPORTANTE: Descomentado e funcionando
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    
    # APIs adicionais para melhor gestão
    path('api/pedido/<int:pedido_id>/status/', views.obter_status_pedido, name='obter_status_pedido'),
    path('api/pedido/<int:pedido_id>/cancelar/', views.cancelar_pedido_api, name='cancelar_pedido_api'),
]