from django.contrib import admin
from django.utils.html import format_html
from .models import Produto, Pedido, ItemPedido, Cupom, CupomUso
import json  # ADICIONAR ESTE IMPORT


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
# ADMIN: PEDIDO (CORRIGIDO - AÇÕES FUNCIONANDO)
# ===============================
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'status', 'valor_total_formatado', 'criado_em', 'nome_entrega', 'cidade_estado']
    list_filter = ['status', 'criado_em', 'cidade', 'estado']
    search_fields = ['usuario__username', 'id', 'nome_entrega', 'endereco', 'cidade', 'estado', 'cep']
    inlines = [ItemPedidoInline]
    
    # CORREÇÃO: Status NÃO está em readonly_fields para permitir ações
    readonly_fields = ['criado_em', 'valor_total', 'preference_id', 'dados_entrega_completo']

    # FIELDSETS CORRIGIDOS - Incluindo todos os campos de endereço
    fieldsets = [
        ('Informações Básicas do Pedido', {
            'fields': [
                'usuario',
                'status',  # AGORA PODE SER EDITADO
                'valor_total',
                'cupom',
                'desconto_cupom',
                'preference_id'
            ]
        }),
        ('📦 DADOS DE ENTREGA - COMPLETO', {
            'fields': ['dados_entrega_completo']
        }),
        ('Campos Individuais de Endereço (Para Edição)', {
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
            ],
            'classes': ['collapse']  # Pode ficar recolhido pois temos o resumo acima
        }),
        ('Datas', {
            'fields': ['criado_em'],
            'classes': ['collapse']
        }),
    ]

    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:.2f}"
    valor_total_formatado.short_description = 'Valor Total'

    def cidade_estado(self, obj):
        if obj.cidade and obj.estado:
            return f"{obj.endereco}, número {obj.numero} - {obj.bairro} - {obj.cidade}/{obj.estado}"
        return "Não informado"
    cidade_estado.short_description = 'Endereço de Entrega'

    def dados_entrega_completo(self, obj):
        """Exibe todos os dados de entrega de forma organizada"""
        
        # Verificar se temos dados básicos
        if not any([obj.nome_entrega, obj.endereco, obj.cidade, obj.estado]):
            return format_html(
                "<div style='background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; color: #856404;'>"
                "<strong>⚠️ ATENÇÃO:</strong> Dados de entrega incompletos ou não preenchidos."
                "</div>"
            )
        
        html = """
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        '>
            <h3 style='margin: 0 0 15px 0; color: white; text-align: center;'>
                🚚 DADOS COMPLETOS PARA ENTREGA
            </h3>
        </div>
        """
        
        # Container principal
        html += """
        <div style='
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        '>
        """
        
        # Grid com duas colunas
        html += """
        <div style='
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        '>
        """
        
        # COLUNA 1: Dados Pessoais
        html += "<div>"
        html += "<h4 style='color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 8px;'>👤 Dados Pessoais</h4>"
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Nome:</strong><br>
            <span style='font-size: 16px; font-weight: bold; color: #2c3e50;'>{obj.nome_entrega or 'NÃO INFORMADO'}</span>
        </div>
        """
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Email:</strong><br>
            <span style='color: #3498db;'>{obj.email_entrega or 'NÃO INFORMADO'}</span>
        </div>
        """
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Telefone:</strong><br>
            <span style='color: #2c3e50;'>{obj.telefone_entrega or 'NÃO INFORMADO'}</span>
        </div>
        """
        html += "</div>"  # Fecha coluna 1
        
        # COLUNA 2: Endereço
        html += "<div>"
        html += "<h4 style='color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 8px;'>📍 Endereço de Entrega</h4>"
        
        # Endereço completo
        endereco_completo = []
        if obj.endereco:
            endereco_completo.append(obj.endereco)
        if obj.numero:
            endereco_completo.append(obj.numero)
        
        endereco_str = ", ".join(endereco_completo) if endereco_completo else "NÃO INFORMADO"
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Endereço:</strong><br>
            <span style='font-size: 16px; font-weight: bold; color: #2c3e50;'>{endereco_str}</span>
        </div>
        """
        
        if obj.complemento:
            html += f"""
            <div style='margin-bottom: 12px;'>
                <strong>Complemento:</strong><br>
                <span style='color: #2c3e50;'>{obj.complemento}</span>
            </div>
            """
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Bairro:</strong><br>
            <span style='color: #2c3e50;'>{obj.bairro or 'NÃO INFORMADO'}</span>
        </div>
        """
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>Cidade/UF:</strong><br>
            <span style='color: #2c3e50;'>{obj.cidade or 'NÃO INFORMADO'} - {obj.estado or 'NÃO INFORMADO'}</span>
        </div>
        """
        
        html += f"""
        <div style='margin-bottom: 12px;'>
            <strong>CEP:</strong><br>
            <span style='color: #2c3e50;'>{obj.cep or 'NÃO INFORMADO'}</span>
        </div>
        """
        html += "</div>"  # Fecha coluna 2
        
        html += "</div>"  # Fecha grid
        html += "</div>"  # Fecha container principal
        
        return format_html(html)
    
    dados_entrega_completo.short_description = '📦 RESUMO DOS DADOS DE ENTREGA'

    # AÇÕES EM MASSA - CORRIGIDAS
    actions = ['marcar_como_pago', 'marcar_como_enviado', 'marcar_como_entregue', 'cancelar_pedido']

    def marcar_como_pago(self, request, queryset):
        """Marca pedidos pendentes como pagos"""
        pedidos_para_atualizar = queryset.filter(status='pendente')
        updated = pedidos_para_atualizar.count()
        
        if updated > 0:
            pedidos_para_atualizar.update(status='pago')
            self.message_user(request, f"✅ {updated} pedido(s) marcado(s) como PAGO.")
        else:
            self.message_user(request, "ℹ️ Nenhum pedido pendente selecionado para marcar como pago.")
    marcar_como_pago.short_description = "💰 Marcar como PAGO (apenas pendentes)"

    def marcar_como_enviado(self, request, queryset):
        """Marca pedidos pagos como enviados"""
        pedidos_para_atualizar = queryset.filter(status='pago')
        updated = pedidos_para_atualizar.count()
        
        if updated > 0:
            pedidos_para_atualizar.update(status='enviado')
            self.message_user(request, f"🚚 {updated} pedido(s) marcado(s) como ENVIADO.")
        else:
            self.message_user(request, "ℹ️ Nenhum pedido pago selecionado para marcar como enviado.")
    marcar_como_enviado.short_description = "📦 Marcar como ENVIADO (apenas pagos)"

    def marcar_como_entregue(self, request, queryset):
        """Marca pedidos pagos ou enviados como entregues"""
        pedidos_para_atualizar = queryset.filter(status__in=['pago', 'enviado'])
        updated = pedidos_para_atualizar.count()
        
        if updated > 0:
            pedidos_para_atualizar.update(status='entregue')
            self.message_user(request, f"🎉 {updated} pedido(s) marcado(s) como ENTREGUE.")
        else:
            self.message_user(request, "ℹ️ Nenhum pedido pago ou enviado selecionado para marcar como entregue.")
    marcar_como_entregue.short_description = "✅ Marcar como ENTREGUE (apenas pagos/enviados)"

    def cancelar_pedido(self, request, queryset):
        """Cancela pedidos pendentes ou pagos"""
        pedidos_para_atualizar = queryset.filter(status__in=['pendente', 'pago'])
        updated = pedidos_para_atualizar.count()
        
        if updated > 0:
            pedidos_para_atualizar.update(status='cancelado')
            self.message_user(request, f"❌ {updated} pedido(s) CANCELADO(s).")
        else:
            self.message_user(request, "ℹ️ Nenhum pedido pendente ou pago selecionado para cancelar.")
    cancelar_pedido.short_description = "🚫 Cancelar pedido(s) (apenas pendentes/pagos)"

    # CORREÇÃO: Adicionar edição rápida na lista
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
# ADMIN: CUPOM DE DESCONTO
# ===============================
@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo', 'valor', 'valor_formatado', 'ativo', 'limite_uso', 'usos_atual', 'data_inicio', 'data_fim']
    list_filter = ['ativo', 'tipo', 'data_inicio', 'data_fim']
    search_fields = ['codigo']
    list_editable = ['ativo', 'valor', 'limite_uso']
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
# ADMIN: USO DO CUPOM
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