from django.contrib import admin
from django.utils.html import format_html
from .models import Produto, Pedido, ItemPedido, Cupom, CupomUso  # NOVO: Cupom e CupomUso


# ===============================
# INLINE: ITENS DO PEDIDO
# ===============================
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['produto', 'quantidade', 'preco_unitario', 'subtotal']

    def subtotal(self, obj):
        return f"R$ {obj.subtotal():.2f}"
    subtotal.short_description = 'Subtotal'


# ===============================
# ADMIN: PEDIDO
# ===============================
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'status', 'status_badge', 'valor_total_formatado', 'criado_em', 'endereco_resumido']
    list_filter = ['status', 'criado_em']
    search_fields = ['usuario__username', 'id', 'nome_entrega', 'endereco', 'cidade', 'cep']
    inlines = [ItemPedidoInline]
    readonly_fields = ['criado_em', 'atualizado_em', 'valor_total', 'id_mercado_pago', 'preference_id', 'status_badge_display']

    fieldsets = [
        ('Informações do Pedido', {
            'fields': [
                'usuario',
                'status',
                'status_badge_display',
                'valor_total',
                'id_mercado_pago',
                'preference_id',
                'cupom',  # NOVO: Mostra cupom usado
                'desconto_cupom'  # NOVO: Mostra desconto
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

    list_editable = ['status']
    date_hierarchy = 'criado_em'


# ===============================
# ADMIN: ITEM DO PEDIDO
# ===============================
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


# ===============================
# ADMIN: PRODUTO
# ===============================
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_formatado', 'estoque', 'disponivel', 'disponivel_badge', 'data_criacao']
    list_filter = ['disponivel', 'data_criacao']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_criacao', 'data_atualizacao']

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

    actions = ['ativar_produtos', 'desativar_produtos']

    def ativar_produtos(self, request, queryset):
        updated = queryset.update(disponivel=True)
        self.message_user(request, f"{updated} produto(s) ativado(s).")
    ativar_produtos.short_description = "Ativar produtos selecionados"

    def desativar_produtos(self, request, queryset):
        updated = queryset.update(disponivel=False)
        self.message_user(request, f"{updated} produto(s) desativado(s).")
    desativar_produtos.short_description = "Desativar produtos selecionados"

    list_editable = ['disponivel']


# ===============================
# NOVO: ADMIN - CUPOM DE DESCONTO
# ===============================
@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo', 'valor', 'valor_formatado', 'ativo', 'limite_uso', 'usos_atual', 'data_inicio', 'data_fim']
    list_filter = ['ativo', 'tipo', 'data_inicio', 'data_fim']
    search_fields = ['codigo']
    list_editable = ['ativo', 'valor', 'limite_uso']  # ← valor está no list_display
    readonly_fields = ['criado_em', 'usos_atual']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'tipo', 'valor')
        }),
        ('Validade', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Limites', {
            'fields': ('limite_uso', 'limite_por_usuario', 'usos_atual')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Datas', {
            'fields': ('criado_em',),
            'classes': ['collapse']
        }),
    )

    def valor_formatado(self, obj):
        if obj.tipo == 'percentual':
            return f"{obj.valor}%"
        return f"R$ {obj.valor:.2f}"
    valor_formatado.short_description = 'Desconto'

    def usos_atual(self, obj):
        return obj.usos.count()
    usos_atual.short_description = 'Usos'


# ===============================
# NOVO: ADMIN - USO DO CUPOM
# ===============================
@admin.register(CupomUso)
class CupomUsoAdmin(admin.ModelAdmin):
    list_display = ['cupom', 'pedido', 'usuario', 'usado_em']
    list_filter = ['usado_em', 'cupom']
    search_fields = ['cupom__codigo', 'pedido__id', 'pedido__usuario__username']
    readonly_fields = ['cupom', 'pedido', 'usado_em']

    def usuario(self, obj):
        return obj.pedido.usuario if obj.pedido.usuario else obj.pedido.email_entrega
    usuario.short_description = 'Cliente'