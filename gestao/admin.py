from django.contrib import admin
from .models import Veiculo, OrdemServico, PecaOS

class PecaOSInline(admin.TabularInline):
    model = PecaOS
    extra = 1
    fields = ('nome_peca', 'quantidade', 'preco_unitario')

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'ano')
    search_fields = ('placa', 'marca')

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('numero_os', 'veiculo', 'status', 'tipo_servico', 'total_geral')
    list_filter = ('status', 'tipo_servico')
    readonly_fields = ('numero_os', 'data_abertura')
    inlines = [PecaOSInline]
    
    fieldsets = (
        ('Identificação', {'fields': ('numero_os', 'veiculo', 'status', 'tipo_servico')}),
        ('Relatório', {'fields': ('descricao_avaria', 'diagnostico_tecnico')}),
        ('Custos', {'fields': ('horas_mao_de_obra', 'valor_hora')}),
    )

@admin.register(PecaOS)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('nome_peca', 'ordem_servico', 'quantidade', 'preco_unitario')