from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('checkout/', views.checkout, name='checkout'),
    path('criar-pagamento/', views.criar_preferencia_pagamento, name='criar_pagamento'),
]
