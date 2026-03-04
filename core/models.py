from django.db import models
from django.contrib.auth.models import User


# ==========================
# PRODUTO
# ==========================
class Produto(models.Model):

    nome = models.CharField(max_length=150)
    codigo_barras = models.CharField(max_length=50, unique=True)

    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)

    estoque = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome


# ==========================
# FORNECEDOR
# ==========================
class Fornecedor(models.Model):

    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# ==========================
# COMPRA
# ==========================
class Compra(models.Model):

    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    data = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Compra {self.id} - {self.fornecedor.nome}"


class ItemCompra(models.Model):

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.IntegerField()
    preco_custo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}"


# ==========================
# CAIXA
# ==========================
class Caixa(models.Model):

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
    ]

    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(blank=True, null=True)

    valor_inicial_dinheiro = models.DecimalField(max_digits=12, decimal_places=2)
    valor_final_dinheiro = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABERTO')

    usuario_abertura = models.ForeignKey(User, on_delete=models.PROTECT, related_name='caixa_abertura')
    usuario_fechamento = models.ForeignKey(User, on_delete=models.PROTECT, related_name='caixa_fechamento', blank=True, null=True)

    def __str__(self):
        return f"Caixa {self.id} - {self.status}"


# ==========================
# VENDA
# ==========================
class Venda(models.Model):

    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    caixa = models.ForeignKey(Caixa, on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data = models.DateTimeField(auto_now_add=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    desconto_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    total_final = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ABERTA')

    def __str__(self):
        return f"Venda {self.id} - {self.status}"


# ==========================
# ITEM VENDA
# ==========================
class ItemVenda(models.Model):

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)

    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_item = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}"


# ==========================
# FORMA DE PAGAMENTO
# ==========================
class FormaPagamento(models.Model):

    nome = models.CharField(max_length=50)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# ==========================
# PAGAMENTO VENDA
# ==========================
class PagamentoVenda(models.Model):

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE)
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.PROTECT)
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.venda.id} - {self.forma_pagamento.nome}"