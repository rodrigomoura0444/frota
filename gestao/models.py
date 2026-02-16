from django.db import models
from django.utils import timezone

class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True, verbose_name="Matrícula")
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    ano = models.PositiveIntegerField(default=2020)

    class Meta:
        verbose_name = "Viatura"
        verbose_name_plural = "Viaturas"

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"

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

    numero_os = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número da OS")
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, verbose_name="Viatura")
    tipo_servico = models.CharField(max_length=20, choices=TIPO_CHOICES, default='REPARACAO')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEBIDO')
    descricao_avaria = models.TextField(verbose_name="Descrição da Avaria")
    diagnostico_tecnico = models.TextField(blank=True, null=True, verbose_name="Diagnóstico Técnico")
    horas_mao_de_obra = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Horas Mão de Obra")
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2, default=40.00, verbose_name="Valor/Hora (€)")
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"

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
        
        if self.status in ['FINALIZADO', 'ENTREGUE'] and not self.data_fechamento:
            self.data_fechamento = timezone.now()
        super().save(*args, **kwargs)

    @property
    def total_pecas(self):
        return sum(p.valor_total for p in self.pecas.all())

    @property
    def total_mao_de_obra(self):
        return self.horas_mao_de_obra * self.valor_hora

    @property
    def total_geral(self):
        return self.total_pecas + self.total_mao_de_obra

    def __str__(self):
        return f"{self.numero_os} - {self.veiculo.placa}"

class PecaOS(models.Model):
    ordem_servico = models.ForeignKey(OrdemServico, related_name='pecas', on_delete=models.CASCADE)
    nome_peca = models.CharField(max_length=100, verbose_name="Nome da Peça")
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário (€)")

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"

    @property
    def valor_total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return self.nome_peca