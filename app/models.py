from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

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
        """Verifica se o produto tem desconto aplicado"""
        return self.preco_original is not None and self.preco_original > self.preco

    def percentual_desconto(self):
        """Calcula o percentual de desconto"""
        if self.tem_desconto():
            return int(((self.preco_original - self.preco) / self.preco_original) * 100)
        return 0

    def estoque_disponivel(self, quantidade=1):
        """Verifica se há estoque disponível para a quantidade solicitada"""
        return self.estoque >= quantidade and self.disponivel

    def reservar_estoque(self, quantidade):
        """Reserva estoque para um pedido"""
        if self.estoque_disponivel(quantidade):
            self.estoque -= quantidade
            self.save()
            return True
        return False

    def liberar_estoque(self, quantidade):
        """Libera estoque reservado"""
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
        on_delete=models.CASCADE,
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
    
    # Integração com Mercado Pago
    id_mercado_pago = models.CharField(
        max_length=100, 
        blank=True,
        default='',
        verbose_name='ID do Mercado Pago'
    )
    preference_id = models.CharField(
        max_length=100, 
        blank=True,
        default='',
        verbose_name='Preference ID'
    )
    
    # Campos de entrega
    nome_entrega = models.CharField(
        max_length=100, 
        verbose_name='Nome para Entrega',
        default=''
    )
    email_entrega = models.EmailField(
        verbose_name='E-mail para Contato',
        default='exemplo@email.com'
    )
    telefone_entrega = models.CharField(
        max_length=20, 
        blank=True,
        default='',
        verbose_name='Telefone para Contato'
    )
    endereco = models.CharField(
        max_length=200, 
        verbose_name='Endereço',
        default=''
    )
    numero = models.CharField(
        max_length=10, 
        verbose_name='Número', 
        default='S/N'
    )
    complemento = models.CharField(
        max_length=100, 
        blank=True,
        default='',
        verbose_name='Complemento'
    )
    bairro = models.CharField(
        max_length=100, 
        verbose_name='Bairro',
        default=''
    )
    cidade = models.CharField(
        max_length=50, 
        verbose_name='Cidade',
        default=''
    )
    estado = models.CharField(
        max_length=50, 
        verbose_name='Estado',
        default=''
    )
    cep = models.CharField(
        max_length=9, 
        verbose_name='CEP',
        default='00000-000'
    )
    
    # Campos adicionais
    observacoes = models.TextField(
        blank=True, 
        default='',
        verbose_name='Observações do Pedido'
    )
    dados_entrega = models.JSONField(
        blank=True, 
        null=True,
        default=dict,
        verbose_name='Dados de Entrega Completos'
    )

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username} - {self.get_status_display()}"

    def calcular_total(self):
        """Calcula o total do pedido baseado nos itens"""
        total = sum(item.subtotal() for item in self.itens.all())
        self.valor_total = total
        self.save()
        return total

    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        endereco = f"{self.endereco}, {self.numero}"
        if self.complemento:
            endereco += f" - {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade} - {self.estado}, CEP: {self.cep}"
        return endereco

    def pode_alterar_status(self, novo_status):
        """Valida se pode alterar para o novo status"""
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
        """Atualiza o status do pedido com validação"""
        if self.pode_alterar_status(novo_status):
            self.status = novo_status
            self.save()
            return True
        return False

    def processar_pagamento_aprovado(self):
        """Processa quando o pagamento é aprovado"""
        if self.status == 'processando':
            self.atualizar_status('pago')
            # Aqui você pode adicionar lógica adicional como enviar e-mail, etc.
            return True
        return False

    def cancelar_pedido(self):
        """Cancela o pedido e libera o estoque"""
        if self.status in ['pendente', 'processando']:
            # Liberar estoque dos itens
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
    pedido = models.ForeignKey(
        Pedido, 
        related_name='itens', 
        on_delete=models.CASCADE,
        verbose_name='Pedido'
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.PROTECT,  # Impede deletar produto com pedidos
        verbose_name='Produto'
    )
    quantidade = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade'
    )
    preco_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Preço Unitário'
    )

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} - Pedido #{self.pedido.id}"

    def subtotal(self):
        """Calcula o subtotal do item"""
        return self.quantidade * self.preco_unitario

    def reservar_estoque(self):
        """Reserva estoque para este item"""
        return self.produto.reservar_estoque(self.quantidade)

    def liberar_estoque(self):
        """Libera estoque reservado para este item"""
        self.produto.liberar_estoque(self.quantidade)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens dos Pedidos'
        constraints = [
            models.UniqueConstraint(
                fields=['pedido', 'produto'], 
                name='unique_produto_pedido'
            )
        ]