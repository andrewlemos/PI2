from django.contrib import admin
from .models import Produto, Pedido

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'estoque']
    list_filter = ['preco']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'status', 'valor_total', 'criado_em']
    list_filter = ['status', 'criado_em']