from django.contrib import admin
from django.utils.html import format_html
from .models import Produto, Pedido, ItemPedido

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['produto', 'quantidade', 'preco_unitario', 'subtotal']
    
    def subtotal(self, obj):
        return f"R$ {obj.subtotal():.2f}"
    subtotal.short_description = 'Subtotal'

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'status', 'status_badge', 'valor_total_formatado', 'criado_em', 'endereco_resumido']
    list_filter = ['status', 'criado_em']
    search_fields = ['usuario__username', 'id', 'nome_entrega', 'endereco', 'cidade', 'cep']
    inlines = [ItemPedidoInline]
    readonly_fields = ['criado_em', 'atualizado_em', 'valor_total', 'id_mercado_pago', 'preference_id', 'status_badge_display']
    
    # Campos editáveis
    fieldsets = [
        ('Informações do Pedido', {
            'fields': [
                'usuario', 
                'status',  # EDITÁVEL
                'status_badge_display',  # APENAS VISUALIZAÇÃO
                'valor_total',
                'id_mercado_pago',
                'preference_id'
            ]
        }),
        ('Datas', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
        ('Informações de Entrega', {
            'fields': [
                'nome_entrega',
                'email_entrega', 
                'telefone_entrega',
                'endereco',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'estado',
                'cep'
            ]
        }),
        ('Outras Informações', {
            'fields': ['observacoes', 'dados_entrega'],
            'classes': ['collapse']
        }),
    ]
    
    # Ações personalizadas
    actions = ['marcar_como_pago', 'marcar_como_enviado', 'marcar_como_entregue', 'cancelar_pedido']
    
    def status_badge(self, obj):
        cores = {
            'pendente': 'gray',
            'processando': 'orange',
            'pago': 'blue', 
            'preparando': 'purple',
            'enviado': 'teal',
            'entregue': 'green',
            'cancelado': 'red',
            'reembolsado': 'brown'
        }
        cor = cores.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status Visual'
    status_badge.admin_order_field = 'status'
    
    def status_badge_display(self, obj):
        """Para exibir no formulário de edição"""
        return self.status_badge(obj)
    status_badge_display.short_description = 'Status Atual'
    
    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:.2f}"
    valor_total_formatado.short_description = 'Valor Total'
    valor_total_formatado.admin_order_field = 'valor_total'
    
    def endereco_resumido(self, obj):
        return f"{obj.cidade} - {obj.estado}"
    endereco_resumido.short_description = 'Localização'
    
    # Ações personalizadas
    def marcar_como_pago(self, request, queryset):
        updated = 0
        for pedido in queryset:
            if pedido.atualizar_status('pago'):
                updated += 1
        self.message_user(request, f"{updated} pedido(s) marcado(s) como pago.")
    marcar_como_pago.short_description = "Marcar como Pago"
    
    def marcar_como_enviado(self, request, queryset):
        updated = 0
        for pedido in queryset:
            if pedido.atualizar_status('enviado'):
                updated += 1
        self.message_user(request, f"{updated} pedido(s) marcado(s) como enviado.")
    marcar_como_enviado.short_description = "Marcar como Enviado"
    
    def marcar_como_entregue(self, request, queryset):
        updated = 0
        for pedido in queryset:
            if pedido.atualizar_status('entregue'):
                updated += 1
        self.message_user(request, f"{updated} pedido(s) marcado(s) como entregue.")
    marcar_como_entregue.short_description = "Marcar como Entregue"
    
    def cancelar_pedido(self, request, queryset):
        updated = 0
        for pedido in queryset:
            if pedido.cancelar_pedido():
                updated += 1
        self.message_user(request, f"{updated} pedido(s) cancelado(s).")
    cancelar_pedido.short_description = "Cancelar Pedido(s)"
    
    # Permite edição rápida do status na lista
    list_editable = ['status']
    
    # Filtros de data
    date_hierarchy = 'criado_em'

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'produto', 'quantidade', 'preco_unitario_formatado', 'subtotal_formatado']
    list_filter = ['pedido__status', 'produto']
    search_fields = ['pedido__id', 'produto__nome']
    
    def preco_unitario_formatado(self, obj):
        return f"R$ {obj.preco_unitario:.2f}"
    preco_unitario_formatado.short_description = 'Preço Unitário'
    
    def subtotal_formatado(self, obj):
        return f"R$ {obj.subtotal():.2f}"
    subtotal_formatado.short_description = 'Subtotal'

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_formatado', 'estoque', 'disponivel', 'disponivel_badge', 'data_criacao']
    list_filter = ['disponivel', 'data_criacao']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    
    # Campos editáveis
    fieldsets = [
        (None, {
            'fields': ['nome', 'descricao', 'preco', 'preco_original', 'desconto']
        }),
        ('Estoque e Disponibilidade', {
            'fields': ['estoque', 'disponivel', 'imagem']
        }),
        ('Datas', {
            'fields': ['data_criacao', 'data_atualizacao'],
            'classes': ['collapse']
        }),
    ]
    
    def preco_formatado(self, obj):
        if obj.tem_desconto():
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">R$ {}</span><br><span style="color: #d32f2f; font-weight: bold;">R$ {}</span>',
                obj.preco_original,
                obj.preco
            )
        return f"R$ {obj.preco:.2f}"
    preco_formatado.short_description = 'Preço'
    
    def disponivel_badge(self, obj):
        if obj.disponivel and obj.estoque > 0:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">Disponível</span>'
            )
        elif obj.disponivel and obj.estoque == 0:
            return format_html(
                '<span style="background-color: #ff9800; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">Esgotado</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #f44336; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">Indisponível</span>'
            )
    disponivel_badge.short_description = 'Status Visual'
    
    # Ações personalizadas
    actions = ['ativar_produtos', 'desativar_produtos']
    
    def ativar_produtos(self, request, queryset):
        updated = queryset.update(disponivel=True)
        self.message_user(request, f"{updated} produto(s) ativado(s).")
    ativar_produtos.short_description = "Ativar produtos selecionados"
    
    def desativar_produtos(self, request, queryset):
        updated = queryset.update(disponivel=False)
        self.message_user(request, f"{updated} produto(s) desativado(s).")
    desativar_produtos.short_description = "Desativar produtos selecionados"
    
    # Permite edição rápida
    list_editable = ['disponivel']