from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import json


class Produto(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome do Produto')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Preço'
    )
    preco_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Preço Original'
    )
    desconto = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Desconto (%)'
    )
    estoque = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade em Estoque'
    )
    imagem = models.ImageField(
        upload_to='produtos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Imagem do Produto'
    )
    disponivel = models.BooleanField(default=True, verbose_name='Disponível para Venda')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"

    def tem_desconto(self):
        return self.preco_original is not None and self.preco_original > self.preco

    def percentual_desconto(self):
        if self.tem_desconto():
            return int(((self.preco_original - self.preco) / self.preco_original) * 100)
        return 0

    def estoque_disponivel(self, quantidade=1):
        return self.estoque >= quantidade and self.disponivel

    def reservar_estoque(self, quantidade):
        if self.estoque_disponivel(quantidade):
            self.estoque -= quantidade
            self.save()
            return True
        return False

    def liberar_estoque(self, quantidade):
        self.estoque += quantidade
        self.save()

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['disponivel', 'estoque']),
            models.Index(fields=['data_criacao']),
        ]


# ===============================
# CUPOM DE DESCONTO (CORRIGIDO)
# ===============================
class Cupom(models.Model):
    TIPO_CHOICES = [
        ('percentual', 'Percentual (%)'),
        ('fixo', 'Valor Fixo (R$)'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código do Cupom'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='percentual',
        verbose_name='Tipo de Desconto'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Valor do Desconto'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_inicio = models.DateField(default=timezone.now, verbose_name='Válido a partir de')  # ← DateField
    data_fim = models.DateField(null=True, blank=True, verbose_name='Válido até')  # ← DateField
    limite_uso = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Limite de Uso (total)'
    )
    limite_por_usuario = models.PositiveIntegerField(
        default=1,
        verbose_name='Limite por Usuário'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.valor} ({self.get_tipo_display()})"

    def is_valid(self, usuario=None):
        agora = timezone.now().date()  # ← .date() aqui!

        if not self.ativo:
            return False, "Cupom inativo"
        if self.data_inicio and agora < self.data_inicio:
            return False, "Cupom ainda não começou"
        if self.data_fim and agora > self.data_fim:
            return False, "Cupom expirado"
        if self.limite_uso is not None:
            usos = self.usos.count()
            if usos >= self.limite_uso:
                return False, "Limite de usos atingido"

        if usuario and usuario.is_authenticated:
            usos_usuario = self.usos.filter(pedido__usuario=usuario).count()
            if usos_usuario >= self.limite_por_usuario:
                return False, "Você já usou este cupom"

        return True, "Válido"

    class Meta:
        verbose_name = 'Cupom de Desconto'
        verbose_name_plural = 'Cupons de Desconto'
        ordering = ['-criado_em']


class CupomUso(models.Model):
    cupom = models.ForeignKey(Cupom, related_name='usos', on_delete=models.CASCADE)
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, related_name='cupom_uso')
    usado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cupom.codigo} usado no pedido #{self.pedido.id}"

    class Meta:
        verbose_name = 'Uso de Cupom'
        verbose_name_plural = 'Usos de Cupom'


# ===============================
# PEDIDO (ENDEREÇO + CUPOM + JSON)
# ===============================
class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando Pagamento'),
        ('pago', 'Pago'),
        ('preparando', 'Preparando Envio'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
        ('reembolsado', 'Reembolsado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Usuário'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status do Pedido'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Valor Total'
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    # Mercado Pago
    id_mercado_pago = models.CharField(max_length=100, blank=True, default='', verbose_name='ID do Mercado Pago')
    preference_id = models.CharField(max_length=100, blank=True, default='', verbose_name='Preference ID')

    # === CAMPOS DE ENTREGA (CORRIGIDOS E OTIMIZADOS) ===
    nome_entrega = models.CharField(max_length=200, blank=True, default='', verbose_name='Nome para Entrega')
    email_entrega = models.EmailField(blank=True, default='', verbose_name='E-mail para Contato')
    telefone_entrega = models.CharField(max_length=20, blank=True, default='', verbose_name='Telefone')
    endereco = models.CharField(max_length=300, blank=True, default='', verbose_name='Endereço')
    numero = models.CharField(max_length=20, blank=True, default='S/N', verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, default='', verbose_name='Complemento')
    bairro = models.CharField(max_length=100, blank=True, default='', verbose_name='Bairro')
    cidade = models.CharField(max_length=100, blank=True, default='', verbose_name='Cidade')
    estado = models.CharField(max_length=2, blank=True, default='', verbose_name='Estado (UF)')
    cep = models.CharField(max_length=9, blank=True, default='', verbose_name='CEP')

    observacoes = models.TextField(blank=True, default='', verbose_name='Observações do Pedido')
    dados_entrega = models.JSONField(blank=True, null=True, default=dict, verbose_name='Dados de Entrega Completos')

    # CUPOM
    cupom = models.ForeignKey(
        Cupom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Cupom Aplicado'
    )
    desconto_cupom = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto do Cupom'
    )

    def __str__(self):
        usuario_nome = self.usuario.username if self.usuario else "Visitante"
        return f"Pedido #{self.id} - {usuario_nome} - {self.get_status_display()}"

    def calcular_total(self):
        subtotal = sum(item.subtotal() for item in self.itens.all())
        desconto = self.desconto_cupom or 0
        self.valor_total = max(subtotal - desconto, 0)
        self.save()
        return self.valor_total

    def endereco_completo(self):
        parts = [self.endereco, self.numero]
        if self.complemento:
            parts.append(self.complemento)
        parts.extend([self.bairro, f"{self.cidade}-{self.estado}", f"CEP: {self.cep}"])
        return ", ".join(filter(None, parts))

    def pode_alterar_status(self, novo_status):
        fluxo_valido = {
            'pendente': ['processando', 'cancelado'],
            'processando': ['pago', 'cancelado'],
            'pago': ['preparando', 'reembolsado'],
            'preparando': ['enviado'],
            'enviado': ['entregue'],
            'entregue': [],
            'cancelado': [],
            'reembolsado': [],
        }
        return novo_status in fluxo_valido.get(self.status, [])

    def atualizar_status(self, novo_status):
        if self.pode_alterar_status(novo_status):
            self.status = novo_status
            self.save()
            return True
        return False

    def processar_pagamento_aprovado(self):
        if self.status == 'processando':
            self.atualizar_status('pago')
            return True
        return False

    def cancelar_pedido(self):
        if self.status in ['pendente', 'processando']:
            for item in self.itens.all():
                item.produto.liberar_estoque(item.quantidade)
            self.atualizar_status('cancelado')
            return True
        return False

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['usuario', 'criado_em']),
            models.Index(fields=['status']),
            models.Index(fields=['id_mercado_pago']),
        ]


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE, verbose_name='Pedido')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, verbose_name='Produto')
    quantidade = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Quantidade')
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name='Preço Unitário')

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} - Pedido #{self.pedido.id}"

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def reservar_estoque(self):
        return self.produto.reservar_estoque(self.quantidade)

    def liberar_estoque(self):
        self.produto.liberar_estoque(self.quantidade)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens dos Pedidos'
        constraints = [
            models.UniqueConstraint(fields=['pedido', 'produto'], name='unique_produto_pedido')
        ]