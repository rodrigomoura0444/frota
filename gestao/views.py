# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import OrdemServico, Veiculo, PecaOS, PecaStock
from xhtml2pdf import pisa
from django.template.loader import get_template, render_to_string
from io import BytesIO
from django.utils import timezone
from datetime import timedelta 
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count
from django.core.mail import EmailMultiAlternatives 
from django.utils.html import strip_tags
from decimal import Decimal
from django.contrib import messages 

# --- FUNÇÕES AUXILIARES ---

def link_callback(uri, rel):
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATIC_ROOT
    if uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        path = uri
    return path if os.path.isfile(path) else uri

def enviar_email_profissional(ordem, mensagem_customizada=None):
    try:
        veiculo = OrdemServico.objects.get(id=ordem.id).veiculo
        cliente_email = veiculo.email_proprietario.strip() if veiculo.email_proprietario else None
        if not cliente_email: return
        
        config_status = {
            'RECEBIDO': {'cor': '#64748b', 'pct': 15},
            'DIAGNOSTICO': {'cor': '#0ea5e9', 'pct': 35},
            'REPARACAO': {'cor': '#2563eb', 'pct': 65},
            'AGUARDANDO_PECAS': {'cor': '#f59e0b', 'pct': 50},
            'FINALIZADO': {'cor': '#10b981', 'pct': 100}
        }
        
        conf = config_status.get(ordem.status, config_status['RECEBIDO'])
        assunto = f"Notificação de Serviço: {veiculo.placa}"
        from_email = settings.EMAIL_HOST_USER
        
        context = {
            'veiculo': veiculo, 
            'os': ordem,
            'cor_destaque': conf['cor'],
            'percentagem': f"{conf['pct']}%",
            'resto_percentagem': f"{100 - conf['pct']}%",
            'texto_informativo': mensagem_customizada or "Informamos que o estado do serviço da sua viatura foi atualizado."
        }

        html_content = render_to_string('emails/os_finalizada.html', context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(assunto, text_content, from_email, [cliente_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Erro e-mail: {e}")

# --- VIEWS PRINCIPAIS ---

def dashboard(request):
    # Lógica de Urgência: Filtramos a fila e identificamos as urgentes para o widget
    fila_espera = OrdemServico.objects.filter(status='RECEBIDO', mecanico__isnull=True).order_by('-prioridade', 'data_abertura')
    urgentes = fila_espera.filter(prioridade='Urgente')
    
    trabalhos_ativos = OrdemServico.objects.filter(
        status__in=['DIAGNOSTICO', 'REPARACAO', 'AGUARDANDO_PECAS'], 
        mecanico__isnull=False
    ).order_by('-prioridade', '-data_atribuicao')

    os_finalizadas = OrdemServico.objects.filter(status='FINALIZADO', data_atribuicao__isnull=False, data_fechamento__isnull=False)
    
    tempo_medio_oficina = 0
    if os_finalizadas.exists():
        tempos = [(os.data_fechamento - os.data_atribuicao).total_seconds() for os in os_finalizadas]
        tempo_medio_oficina = (sum(tempos) / len(tempos)) / 3600

    # CORREÇÃO: Usando 'ordens_atribuidas' conforme definido no related_name do modelo
    mecanicos = User.objects.annotate(
        total_servicos=Count('ordens_atribuidas', filter=Q(ordens_atribuidas__status='FINALIZADO'))
    ).order_by('-total_servicos')

    # --- NOVO: CÁLCULO DE CAPACIDADE E ATIVIDADE ---
    total_mecanicos = User.objects.count()
    mecanicos_ocupados = trabalhos_ativos.values('mecanico').distinct().count()
    capacidade = int((mecanicos_ocupados / total_mecanicos * 100)) if total_mecanicos > 0 else 0
    
    # Busca as últimas 5 atribuições para o feed lateral
    atividade_recente = OrdemServico.objects.filter(
        mecanico__isnull=False
    ).order_by('-data_atribuicao')[:5]

    return render(request, 'dashboard.html', {
        'fila': fila_espera,
        'urgentes': urgentes,
        'trabalhos_ativos': trabalhos_ativos,
        'mecanicos': mecanicos,
        'tempo_medio': round(tempo_medio_oficina, 1), 
        'capacidade': capacidade, # Passado para o gráfico de ocupação
        'atividade_recente': atividade_recente, # Passado para o feed lateral
    })

def atribuir_mecanico(request):
    if request.method == "POST":
        os_id = request.POST.get('os_id')
        mecanico_id = request.POST.get('mecanico_id')
        ordem = get_object_or_404(OrdemServico, id=os_id)
        
        if ordem.status_pecas == 'vermelho': 
            messages.error(request, f"BLOQUEIO: A viatura {ordem.veiculo.placa} não tem peças em stock!")
            return redirect('dashboard')
            
        ordem.mecanico = get_object_or_404(User, id=mecanico_id)
        ordem.status = 'DIAGNOSTICO' 
        ordem.data_atribuicao = timezone.now()
        
        # Se for urgente, garantimos que a flag de processamento seja prioritária
        if ordem.prioridade == 'Urgente':
            messages.warning(request, f"ALERTA: Pista Rápida acionada para o técnico {ordem.mecanico.username}!")
        
        ordem.save() 
        
        messages.success(request, f"Técnico {ordem.mecanico.username} atribuído!")
        
        msg_inicio = f"Informamos que a reparação da viatura {ordem.veiculo.placa} teve início ({ordem.prioridade}) sob a responsabilidade do técnico {ordem.mecanico.username}."
        enviar_email_profissional(ordem, mensagem_customizada=msg_inicio)
        
        request.session['os_id_atual'] = ordem.id
        return redirect('detalhe_os_sessao')
        
    return redirect('dashboard')

def finalizar_os(request):
    os_id = request.POST.get('os_id') or request.session.get('os_id_atual')
    if not os_id: 
        messages.error(request, "Erro: Ordem de Serviço não identificada.")
        return redirect('dashboard')
        
    ordem = get_object_or_404(OrdemServico, id=os_id)
    
    if request.method == "POST":
        # 1. Atualizar Peças Existentes
        for peca in ordem.pecas.all():
            peca.marca = request.POST.get(f'marca_{peca.id}', peca.marca)
            qtd_form = request.POST.get(f'qtd_{peca.id}')
            if qtd_form:
                try: 
                    peca.quantidade = Decimal(str(qtd_form).replace(',', '.'))
                except: pass
            peca.confirmado = True if request.POST.get(f'confirmado_{peca.id}') else False
            peca.save()

        # 2. Nova Peça Extra
        nova_peca_nome = request.POST.get('nova_peca_nome')
        if nova_peca_nome:
            nova_peca_marca = request.POST.get('nova_peca_marca', '')
            nova_peca_qtd = request.POST.get('nova_peca_qtd', 1)
            try:
                qtd_dec = Decimal(str(nova_peca_qtd).replace(',', '.'))
                PecaOS.objects.create(
                    ordem_servico=ordem,
                    nome_peca=nova_peca_nome,
                    marca=nova_peca_marca,
                    quantidade=qtd_dec,
                    confirmado=True
                )
                messages.success(request, f"Peça {nova_peca_nome} adicionada!")
            except: pass

        # 3. Diagnóstico e Horas
        ordem.diagnostico_tecnico = request.POST.get('diagnostico_tecnico', '')
        horas_raw = request.POST.get('horas_mao_de_obra')
        if horas_raw:
            try: 
                ordem.horas_mao_de_obra = Decimal(str(horas_raw).replace(',', '.'))
            except: pass
            
        # 4. Finalização ou Rascunho
        if request.POST.get('botao_finalizar') == "true":
            for p_os in ordem.pecas.all():
                if p_os.peca_referencia:
                    p_stock = p_os.peca_referencia
                    p_stock.quantidade_em_stock -= p_os.quantidade
                    p_stock.save()

            ordem.status = 'FINALIZADO'
            ordem.data_fechamento = timezone.now()
            ordem.save()
            
            hora_pronto = (timezone.now() + timedelta(minutes=15)).strftime('%H:%M')
            msg_fim = f"Excelente notícia! A manutenção da viatura {ordem.veiculo.placa} foi concluída. Disponível a partir das {hora_pronto}h."
            enviar_email_profissional(ordem, mensagem_customizada=msg_fim)
            
            if 'os_id_atual' in request.session:
                del request.session['os_id_atual']

            messages.info(request, f"Trabalho na OS {ordem.numero_os} finalizado!")
            return redirect('dashboard')
            
        ordem.save()
        messages.success(request, "Progresso guardado.")
        return redirect('detalhe_os_sessao')
        
    return redirect('dashboard')

def abrir_detalhe_os(request, os_id):
    request.session['os_id_atual'] = os_id
    return redirect('detalhe_os_sessao')

def detalhe_os(request):
    os_id = request.session.get('os_id_atual')
    if not os_id: return redirect('dashboard')
    os_instancia = get_object_or_404(OrdemServico, id=os_id)
    return render(request, 'os/detalhe_os.html', {'os': os_instancia})

def lista_os(request):
    ordens = OrdemServico.objects.all().order_by('-data_abertura')
    return render(request, 'lista_os.html', {'ordens': ordens})

def clientes(request):
    query = request.GET.get('q')
    veiculos = Veiculo.objects.all()
    if query:
        veiculos = veiculos.filter(Q(placa__icontains=query) | Q(proprietario__icontains=query))
    return render(request, 'clientes.html', {'veiculos': veiculos.order_by('placa'), 'query': query})

def acompanhar_reparacao(request, os_numero):
    ordem = get_object_or_404(OrdemServico, numero_os=os_numero)
    progresso_map = {'RECEBIDO': 15, 'DIAGNOSTICO': 35, 'REPARACAO': 65, 'AGUARDANDO_PECAS': 50, 'FINALIZADO': 100}
    context = {'os': ordem, 'percentagem': progresso_map.get(ordem.status, 0)}
    return render(request, 'os/acompanhar_publico.html', context)

def gerar_pdf_os(request, os_id):
    os_instancia = get_object_or_404(OrdemServico, id=os_id)
    template = get_template('os_pdf.html')
    html = template.render({'os': os_instancia, 'pecas': os_instancia.pecas.all()})
    result = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8', link_callback=link_callback)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="OS_{os_instancia.numero_os}.pdf"'
    return response