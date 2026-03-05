# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from decimal import Decimal

# Modelo: Veículo
class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True, verbose_name="Matrícula")
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    ano = models.PositiveIntegerField(default=2020)
    km_atual = models.PositiveIntegerField(default=0, verbose_name="Quilometragem Atual")
    proprietario = models.CharField(max_length=100, verbose_name="Nome do Proprietário", default="Cliente")
    telemovel_proprietario = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telemóvel para SMS")
    email_proprietario = models.EmailField(max_length=254, blank=True, null=True)

    class Meta:
        verbose_name = "Viatura"
        verbose_name_plural = "Viaturas"

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"

# Modelo: Peça em Stock
class PecaStock(models.Model):
    nome = models.CharField(max_length=100)
    referencia = models.CharField(max_length=50, unique=True, verbose_name="Referência/SKU")
    quantidade_em_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda_padrao = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Peça em Stock"
        verbose_name_plural = "Peças em Stock"

    def __str__(self):
        return f"{self.nome} (Ref: {self.referencia}) - Qtd: {self.quantidade_em_stock}"

# Modelo: Ordem de Serviço
class OrdemServico(models.Model):
    TIPO_CHOICES = [
        ('REPARACAO', 'Reparação Corretiva'), 
        ('MANUTENCAO', 'Manutenção Preventiva'), 
        ('GARANTIA', 'Garantia')
    ]
    STATUS_CHOICES = [
        ('RECEBIDO', 'Recebido'), 
        ('DIAGNOSTICO', 'Em diagnóstico'),
        ('REPARACAO', 'Em reparação'), 
        ('AGUARDANDO_PECAS', 'A aguardar peças'), 
        ('FINALIZADO', 'Finalizado'), 
        ('ENTREGUE', 'Entregue'),
    ]
    PRIORIDADE_CHOICES = [
        ('Normal', 'Normal'),
        ('Urgente', 'Urgente'),
    ]

    numero_os = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número da OS")
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, verbose_name="Viatura")
    
    mecanico = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Mecânico Atribuído",
        related_name="ordens_atribuidas"
    )
    
    tipo_servico = models.CharField(max_length=20, choices=TIPO_CHOICES, default='REPARACAO')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='Normal', verbose_name="Prioridade")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEBIDO')
    descricao_avaria = models.TextField(verbose_name="Descrição da Avaria")
    diagnostico_tecnico = models.TextField(blank=True, null=True, verbose_name="Diagnóstico Técnico")
    
    horas_mao_de_obra = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Horas Mão de Obra")
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2, default=40.00, verbose_name="Valor/Hora (€)")
    
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_atribuicao = models.DateTimeField(blank=True, null=True, verbose_name="Início do Trabalho")
    data_fechamento = models.DateTimeField(blank=True, null=True, verbose_name="Fim do Trabalho")

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"

    @property
    def status_pecas(self):
        pecas_da_os = self.pecas.all()
        if not pecas_da_os.exists():
            return 'verde'
        total_pecas = pecas_da_os.count()
        disponiveis = 0
        for p in pecas_da_os:
            if p.peca_referencia:
                if p.peca_referencia.quantidade_em_stock >= p.quantidade:
                    disponiveis += 1
        if disponiveis == total_pecas:
            return 'verde'
        elif disponiveis > 0:
            return 'amarelo'
        else:
            return 'vermelho'

    def save(self, *args, **kwargs):
        if not self.numero_os:
            ano_atual = timezone.now().year
            ultima_os = OrdemServico.objects.filter(numero_os__startswith=f"OS-{ano_atual}").order_by('-numero_os').first()
            if ultima_os:
                try:
                    ultimo_numero = int(ultima_os.numero_os.split('-')[-1])
                    novo_numero = ultimo_numero + 1
                except: novo_numero = 1
            else: novo_numero = 1
            self.numero_os = f"OS-{ano_atual}-{novo_numero:03d}"
            
        if not self.status:
            self.status = 'RECEBIDO'

        status_ativos = ['DIAGNOSTICO', 'REPARACAO', 'AGUARDANDO_PECAS']
        if self.status in status_ativos and self.mecanico and not self.data_atribuicao:
            self.data_atribuicao = timezone.now()

        if self.status in ['FINALIZADO', 'ENTREGUE'] and not self.data_fechamento:
            self.data_fechamento = timezone.now()
            
        super().save(*args, **kwargs)

    @property
    def hora_prevista_entrega(self):
        if self.data_atribuicao:
            estimativa_base = 1.0 if self.prioridade == 'Urgente' else 2.0
            estimativa = float(self.horas_mao_de_obra) if self.horas_mao_de_obra > 0 else estimativa_base
            return self.data_atribuicao + timedelta(hours=estimativa)
        return None

    @property
    def total_pecas(self):
        return sum(p.valor_total for p in self.pecas.all()) or Decimal('0.00')

    @property
    def total_mao_de_obra(self):
        return self.horas_mao_de_obra * self.valor_hora

    @property
    def total_geral(self):
        return self.total_pecas + self.total_mao_de_obra

    # --- NOVAS PROPRIEDADES PARA RESOLVER O ERRO DO TEMPLATE (OPÇÃO 1) ---
    @property
    def numero_os_limpo(self):
        """Retorna apenas o número final da OS (ex: 001)"""
        if self.numero_os:
            return self.numero_os.split('-')[-1]
        return ""

    @property
    def ano_os(self):
        """Retorna apenas o ano da OS (ex: 2026)"""
        if self.numero_os:
            parts = self.numero_os.split('-')
            if len(parts) > 1:
                return parts[1]
        return ""

    def __str__(self):
        return f"{self.numero_os} - {self.veiculo.placa} ({self.prioridade})"

# Modelo: Peça na Ordem de Serviço
class PecaOS(models.Model):
    ordem_servico = models.ForeignKey(OrdemServico, related_name='pecas', on_delete=models.CASCADE)
    peca_referencia = models.ForeignKey(PecaStock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vincular ao Stock")
    
    nome_peca = models.CharField(max_length=100, verbose_name="Nome da Peça")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca Utilizada")
    quantidade = models.DecimalField(max_digits=7, decimal_places=2, default=1, verbose_name="Qtd")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço Unitário (€)")
    confirmado = models.BooleanField(default=False, verbose_name="Confirmado")

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"

    @property
    def valor_total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.nome_peca} (OS {self.ordem_servico.numero_os})"

# Modelo: Detalhe da Intervenção
class DetalheIntervencao(models.Model):
    ordem_servico = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, related_name='detalhe_planeamento')
    diagnostico_detalhado = models.TextField(blank=True, null=True)
    garantia_aplicavel = models.BooleanField(default=False)
    proxima_revisao_km = models.PositiveIntegerField(blank=True, null=True)
    proxima_revisao_data = models.DateField(blank=True, null=True)
    alertas_ativos = models.BooleanField(default=True)

    def __str__(self):
        return f"Detalhe OS #{self.ordem_servico.numero_os}"