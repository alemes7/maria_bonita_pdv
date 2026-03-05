from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum


# ==========================
# PRODUTO
# ==========================
class Produto(models.Model):

    nome = models.CharField(max_length=150)
    codigo_barras = models.CharField(max_length=50, unique=True)

    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)

    estoque = models.PositiveIntegerField(default=0)
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

    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Compra {self.id} - {self.fornecedor.nome if self.fornecedor else 'Sem fornecedor'}"


class ItemCompra(models.Model):

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
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

    def save(self, *args, **kwargs):
        # Validar que não há outra caixa aberta
        if self.status == 'ABERTO':
            caixa_aberta = Caixa.objects.filter(status='ABERTO').exclude(pk=self.pk).exists()
            if caixa_aberta:
                raise ValidationError("Já existe um caixa aberto. Feche o caixa anterior antes de abrir um novo.")
        
        super().save(*args, **kwargs)

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

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    desconto_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    total_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ABERTA')

    def save(self, *args, **kwargs):
        # Validar quando finalizar a venda
        if self.status == 'FINALIZADA':
            # Verificar se caixa está aberto
            if self.caixa.status != 'ABERTO':
                raise ValidationError("O caixa deve estar aberto para finalizar uma venda.")
            
            # Verificar se há pagamento registrado
            pagamentos = PagamentoVenda.objects.filter(venda=self).aggregate(total=Sum('valor'))['total'] or 0
            if pagamentos < self.total_final:
                raise ValidationError(f"Pagamento insuficiente. Faltam R$ {self.total_final - pagamentos:.2f}")
        
        super().save(*args, **kwargs)

    def atualizar_totais(self):
        subtotal = self.itens.aggregate(
            total=Sum('total_item')
        )['total'] or 0

        self.subtotal = subtotal

        if self.desconto_percentual:
            desconto = subtotal * (self.desconto_percentual / 100)
            self.total_final = subtotal - desconto
        else:
            self.total_final = subtotal - self.desconto_valor

        self.save(update_fields=['subtotal', 'total_final'])

    def __str__(self):
        return f"Venda {self.id} - {self.status}"


# ==========================
# ITEM VENDA
# ==========================
class ItemVenda(models.Model):

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)

    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_item = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):

        if self.venda.status == 'FINALIZADA':
            raise ValidationError("Não é possível editar itens de uma venda finalizada.")

        if self.pk:
            # Já existe (edição)
            item_antigo = ItemVenda.objects.get(pk=self.pk)
            diferenca = self.quantidade - item_antigo.quantidade
        else:
            # Novo item
            diferenca = self.quantidade

        if diferenca > 0 and diferenca > self.produto.estoque:
            raise ValidationError("Estoque insuficiente.")

        # Define preço automático
        if not self.preco_unitario:
            self.preco_unitario = self.produto.preco_venda

        self.total_item = self.quantidade * self.preco_unitario

        super().save(*args, **kwargs)

        # Atualiza estoque corretamente
        self.produto.estoque -= diferenca
        self.produto.save()

        # Atualiza totais da venda
        self.venda.atualizar_totais()

    def delete(self, *args, **kwargs):
        if self.venda.status == 'FINALIZADA':
            raise ValidationError("Não é possível excluir itens de uma venda finalizada.")

        self.produto.estoque += self.quantidade
        self.produto.save()

        super().delete(*args, **kwargs)

        self.venda.atualizar_totais()

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

    def save(self, *args, **kwargs):
        if self.venda.status == 'FINALIZADA':
            raise ValidationError("Não é possível alterar pagamentos de uma venda finalizada.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.venda.status == 'FINALIZADA':
            raise ValidationError("Não é possível excluir pagamentos de uma venda finalizada.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.venda.id} - {self.forma_pagamento.nome}"