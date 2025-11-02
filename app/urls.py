from django.urls import path
from . import views

#app_name = 'app'  # Namespace para evitar conflitos (recomendado)

urlpatterns = [
    # ===============================
    # PÁGINAS PRINCIPAIS
    # ===============================
    path('', views.index, name='index'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('checkout/', views.checkout, name='checkout'),

    # ===============================
    # STATUS DA COMPRA
    # ===============================
    path('compra-confirmada/', views.compra_confirmada, name='compra_confirmada'),
    path('compra-erro/', views.compra_erro, name='compra_erro'),
    path('compra-pendente/', views.compra_pendente, name='compra_pendente'),

    # ===============================
    # GESTÃO DE PEDIDOS (requer login)
    # ===============================
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),

    # ===============================
    # ATALHOS AMIGÁVEIS PARA LOGIN/LOGOUT (OPCIONAL)
    # Redireciona para o allauth, mas com URLs mais limpas
    # ===============================
    path('entrar/', views.login_redirect, name='login'),  # /entrar/
    path('sair/', views.logout_redirect, name='logout'),  # /sair/

    # ===============================
    # APIs - PAGAMENTO
    # ===============================
    path('api/criar-preferencia-pagamento/', views.criar_preferencia_pagamento, name='criar_preferencia_pagamento'),
    #path('api/finalizar-compra/', views.finalizar_compra, name='finalizar_compra'),

    # ===============================
    # APIs - ESTOQUE E PRODUTOS
    # ===============================
    path('api/verificar-estoque/', views.verificar_estoque, name='verificar_estoque'),
    path('api/atualizar-estoque-carrinho/', views.atualizar_estoque_carrinho, name='atualizar_estoque_carrinho'),
    path('api/buscar-sugestoes/', views.buscar_sugestoes, name='buscar_sugestoes'),

    # ===============================
    # WEBHOOK MERCADO PAGO
    # ===============================
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),

    # ===============================
    # APIs - GESTÃO DE PEDIDOS
    # ===============================
    path('api/pedido/<int:pedido_id>/status/', views.obter_status_pedido, name='obter_status_pedido'),
    path('api/pedido/<int:pedido_id>/cancelar/', views.cancelar_pedido_api, name='cancelar_pedido_api'),
    path('api/aplicar-cupom/', views.aplicar_cupom, name='api_aplicar_cupom'),
]