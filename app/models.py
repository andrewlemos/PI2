from django.db import models
from django.contrib.auth.models import User

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    preco_original = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    desconto = models.IntegerField(null=True, blank=True)
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
    
    def tem_desconto(self):
        return self.preco_original is not None and self.preco_original > self.preco
    
    def percentual_desconto(self):
        if self.tem_desconto():
            return int(((self.preco_original - self.preco) / self.preco_original) * 100)
        return 0

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_criacao']

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('cancelado', 'Cancelado'),
        ('entregue', 'Entregue'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    id_mercado_pago = models.CharField(max_length=100, blank=True)

    # Campos de entrega
    nome_entrega = models.CharField(max_length=100)
    email_entrega = models.EmailField()
    endereco = models.CharField(max_length=200)
    cidade = models.CharField(max_length=50)
    estado = models.CharField(max_length=50)
    cep = models.CharField(max_length=9, default='00000-000')

    def __str__(self):
        return f"Pedido {self.id} - {self.usuario.username}"
    
    def calcular_total(self):
        total = sum(item.subtotal() for item in self.itens.all())
        self.valor_total = total
        self.save()
        return total

    def endereco_completo(self):
        return f"{self.endereco}, {self.cidade} - {self.estado}, CEP: {self.cep}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens dos Pedidos'
