from django.contrib import admin
from .models import Produto, Pedido, ItemPedido

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['produto', 'quantidade', 'preco_unitario', 'subtotal']
    
    def subtotal(self, obj):
        return obj.subtotal()
    subtotal.short_description = 'Subtotal'

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'status', 'valor_total', 'criado_em', 'endereco_completo']
    list_filter = ['status', 'criado_em']
    search_fields = ['usuario__username', 'id', 'nome_entrega', 'endereco', 'cidade', 'cep']
    inlines = [ItemPedidoInline]
    readonly_fields = ['criado_em', 'atualizado_em', 'valor_total']

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'produto', 'quantidade', 'preco_unitario', 'subtotal']
    list_filter = ['pedido__status']
    
    def subtotal(self, obj):
        return obj.subtotal()
    subtotal.short_description = 'Subtotal'

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'estoque', 'disponivel', 'data_criacao']
    list_filter = ['disponivel', 'data_criacao']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_criacao', 'data_atualizacao']
