from django.test import TestCase
from django.contrib.auth.models import User
from .models import Produto

class ProdutoModelTest(TestCase):
    def setUp(self):
        self.produto = Produto.objects.create(
            nome="Teste Produto",
            preco=10.99,
            estoque=10
        )

    def test_produto_creation(self):
        self.assertEqual(self.produto.nome, "Teste Produto")
        self.assertEqual(self.produto.preco, 10.99)
        self.assertEqual(self.produto.estoque, 10)
