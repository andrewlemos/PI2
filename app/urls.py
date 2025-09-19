from django.urls import path
from . import views
from .views import buscar_sugestoes  # ← Adicione esta importação

urlpatterns = [
    path('', views.index, name='index'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('checkout/', views.checkout, name='checkout'),
    path('criar-pagamento/', views.criar_preferencia_pagamento, name='criar_pagamento'),
    path('api/buscar-sugestoes/', buscar_sugestoes, name='buscar_sugestoes'),  # ← Nova URL
]