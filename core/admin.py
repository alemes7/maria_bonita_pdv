from django.contrib import admin
from .models import (
    Produto,
    Fornecedor,
    Compra,
    ItemCompra,
    Caixa,
    Venda,
    ItemVenda,
    FormaPagamento,
    PagamentoVenda
)

# ==========================
# PRODUTO
# ==========================
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'codigo_barras', 'preco_venda', 'estoque', 'ativo')
    search_fields = ('nome', 'codigo_barras')
    list_filter = ('ativo',)
    ordering = ('nome',)


# ==========================
# FORNECEDOR
# ==========================
@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'telefone', 'email', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)


# ==========================
# ITEM COMPRA INLINE
# ==========================
class ItemCompraInline(admin.TabularInline):
    model = ItemCompra
    extra = 1


# ==========================
# COMPRA
# ==========================
@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'fornecedor', 'data', 'valor_total')
    inlines = [ItemCompraInline]


# ==========================
# ITEM VENDA INLINE
# ==========================
class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1


class PagamentoVendaInline(admin.TabularInline):
    model = PagamentoVenda
    extra = 1


# ==========================
# VENDA
# ==========================
@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'caixa', 'usuario', 'data', 'total_final', 'status')
    list_filter = ('status',)
    inlines = [ItemVendaInline, PagamentoVendaInline]


# ==========================
# CAIXA
# ==========================
@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_abertura', 'status', 'usuario_abertura')
    list_filter = ('status',)


# ==========================
# FORMA PAGAMENTO
# ==========================
@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'ativo')
    list_filter = ('ativo',)

