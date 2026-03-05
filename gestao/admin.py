# Configuração do Django Admin
# Interface de administração do sistema
# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import OrdemServico, Veiculo, PecaOS, PecaStock, DetalheIntervencao
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Admin para gestão de stock de peças
@admin.register(PecaStock)
class PecaStockAdmin(admin.ModelAdmin):
    list_display = ('nome', 'referencia', 'quantidade_em_stock', 'preco_venda_padrao', 'status_visual')
    search_fields = ('nome', 'referencia')
    list_filter = ('quantidade_em_stock',)

    def status_visual(self, obj):
        if obj.quantidade_em_stock <= 0:
            return mark_safe('<b style="color: #dc3545;">ESGOTADO</b>')
        elif obj.quantidade_em_stock < 5:
            return mark_safe('<b style="color: #fd7e14;">BAIXO STOCK</b>')
        return mark_safe('<b style="color: #28a745;">OK</b>')
    
    status_visual.short_description = 'Status de Inventário'

# Inline para editar peças dentro da OS
class PecaOSInline(admin.TabularInline):
    model = PecaOS
    fields = ('peca_referencia', 'nome_peca', 'marca', 'quantidade', 'preco_unitario', 'confirmado')
    autocomplete_fields = ['peca_referencia'] # Facilita a busca se tiveres muitas peças
    extra = 0

# Admin para Ordens de Serviço
@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    # Adicionada 'prioridade_visual' na lista para destaque imediato
    list_display = ('numero_os', 'veiculo', 'tipo_servico', 'prioridade_visual', 'status', 'status_logistico_semaforo', 'mecanico', 'tempo_permanencia_formatado')
    list_filter = ('status', 'prioridade', 'tipo_servico', 'mecanico', 'data_abertura')
    search_fields = ('numero_os', 'veiculo__placa', 'veiculo__proprietario')
    inlines = [PecaOSInline]
    
    # Organização dos campos no formulário de edição
    fieldsets = (
        ('Identificação Básica', {
            # 'prioridade' inserida aqui para aparecer no formulário
            'fields': (('numero_os', 'status'), ('veiculo', 'mecanico'), ('tipo_servico', 'prioridade'))
        }),
        ('Relatórios e Diagnósticos', {
            'fields': ('descricao_avaria', 'diagnostico_tecnico')
        }),
        ('Custos e Mão de Obra', {
            'fields': (('horas_mao_de_obra', 'valor_hora'),)
        }),
        ('Controlo Temporal', {
            'fields': (('data_abertura', 'data_atribuicao', 'data_fechamento'), 'tempo_total_detalhado'),
            'description': 'Datas geradas automaticamente pelo sistema conforme o progresso do trabalho.'
        }),
    )

    readonly_fields = ('data_abertura', 'data_atribuicao', 'data_fechamento', 'tempo_total_detalhado', 'status_logistico_semaforo')

    # Destaque visual para a prioridade na lista
    def prioridade_visual(self, obj):
        if obj.prioridade == 'Urgente':
            return mark_safe('<span style="color: #fff; background: #dc3545; padding: 2px 6px; border-radius: 4px; font-weight: bold;">⚡ URGENTE</span>')
        return "Normal"
    
    prioridade_visual.short_description = 'Prioridade'

    # Semáforo lógico (verde/amarelo/vermelho) para peças
    def status_logistico_semaforo(self, obj):
        status = obj.status_pecas 
        if status == 'verde':
            return mark_safe('<span style="color: #28a745; font-weight: bold;">● OK</span>')
        elif status == 'amarelo':
            return mark_safe('<span style="color: #ffc107; font-weight: bold;">● Pendente</span>')
        else:
            return mark_safe('<span style="color: #dc3545; font-weight: bold;">● FALTA STOCK</span>')
    
    status_logistico_semaforo.short_description = 'Check Peças'

    def tempo_permanencia_formatado(self, obj):
        if not obj.data_abertura:
            return "---"
        fim = obj.data_fechamento if obj.data_fechamento else timezone.now()
        diff = fim - obj.data_abertura
        dias = diff.days
        horas = diff.seconds // 3600
        if dias > 0:
            return f"{dias}d {horas}h"
        return f"{horas}h"
    
    tempo_permanencia_formatado.short_description = 'Permanência'

    def tempo_total_detalhado(self, obj):
        if obj.data_abertura and obj.data_fechamento:
            diff = obj.data_fechamento - obj.data_abertura
            dias = diff.days
            horas, resto = divmod(diff.seconds, 3600)
            minutos, _ = divmod(resto, 60)
            return f"Viatura esteve na oficina durante: {dias} dias, {horas} horas e {minutos} minutos."
        elif obj.data_abertura:
            diff = timezone.now() - obj.data_abertura
            return f"Viatura ainda em reparação (Há {diff.days} dias e {diff.seconds // 3600} horas)."
        return "Dados insuficientes."

    tempo_total_detalhado.short_description = 'Tempo Total de Estadia'

# Admin para Veículos
@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'proprietario')
    search_fields = ('placa', 'proprietario')

# Admin para Detalhes de Intervenção
@admin.register(DetalheIntervencao)
class DetalheIntervencaoAdmin(admin.ModelAdmin):
    list_display = ('ordem_servico', 'proxima_revisao_data', 'garantia_aplicavel')