import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import OrdemServico, Veiculo
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO
from django.utils import timezone

# FUNÇÃO AUXILIAR: Resolve o problema do Logo não aparecer no PDF
def link_callback(uri, rel):
    """
    Converte URIs de ficheiros estáticos em caminhos absolutos do sistema.
    """
    # Encontra o caminho para a pasta static
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]

    if uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        path = uri

    # Verifica se o ficheiro existe realmente
    if not os.path.isfile(path):
        return uri
    return path

# 1. DASHBOARD PROFISSIONAL
def dashboard(request):
    veiculos = Veiculo.objects.all()
    todas_as_ordens = OrdemServico.objects.all()
    
    # KPIs Profissionais
    faturamento_total = sum(os.total_geral for os in todas_as_ordens if os.status in ['FINALIZADO', 'ENTREGUE'])
    
    # Contadores de Urgência
    viaturas_paradas = todas_as_ordens.filter(status='AGUARDANDO_PECAS').count()
    em_reparacao = todas_as_ordens.filter(status='REPARACAO').count()
    
    # Puxa as 5 ordens mais recentes
    ordens_recentes = todas_as_ordens.order_by('-data_abertura')[:5]
    
    return render(request, 'dashboard.html', {
        'veiculos': veiculos,
        'ordens': ordens_recentes,
        'faturamento_total': faturamento_total,
        'parados': viaturas_paradas,
        'em_curso': em_reparacao,
    })

# 2. DETALHE DA OS
def detalhe_os(request, pk):
    os_instancia = get_object_or_404(OrdemServico, pk=pk)
    return render(request, 'detalhe_os.html', {'os': os_instancia})

# 3. LISTA DE TODAS AS OS
def lista_os(request):
    ordens = OrdemServico.objects.all().order_by('-data_abertura')
    return render(request, 'lista_os.html', {'ordens': ordens})

# 4. VIEW DE CLIENTES
def clientes(request):
    return render(request, 'clientes.html')

# 5. GERAR PDF (Agora com suporte para Logo e UTF-8)
def gerar_pdf_os(request, os_id):
    os_instancia = get_object_or_404(OrdemServico, id=os_id)
    
    context = {
        'os': os_instancia,
        'pecas': os_instancia.pecas.all(),
        'total_pecas': os_instancia.total_pecas,
        'total_mo': os_instancia.total_mao_de_obra,
        'total_geral': os_instancia.total_geral,
    }
    
    template = get_template('os_pdf.html')
    html = template.render(context)
    result = BytesIO()
    
    # Adicionámos o link_callback para processar as imagens (Logo)
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), 
        result, 
        encoding='UTF-8',
        link_callback=link_callback
    )
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"{os_instancia.numero_os}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("Erro técnico ao gerar o PDF da Ordem de Serviço.", status=400)