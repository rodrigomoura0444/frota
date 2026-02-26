import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import OrdemServico, Veiculo, PecaOS, PecaStock  # Adicionado PecaStock
from xhtml2pdf import pisa
from django.template.loader import get_template, render_to_string
from io import BytesIO
from django.utils import timezone
from datetime import timedelta 
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives 
from django.utils.html import strip_tags
from decimal import Decimal
from django.contrib import messages 

# --- FUNÇÕES AUXILIARES ---

def link_callback(uri, rel):
    """ Auxiliar para converter caminhos estáticos para o PDF """
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATIC_ROOT
    if uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        path = uri
    return path if os.path.isfile(path) else uri

def enviar_email_profissional(ordem, mensagem_customizada=None):
    """ Envia e-mail FORMAL e RESPONSIVO (Mobile/Desktop) """
    try:
        veiculo = Veiculo.objects.get(id=ordem.veiculo.id)
        cliente_email = veiculo.email_proprietario.strip() if veiculo.email_proprietario else None

        if not cliente_email: 
            return
        
        link_status = f"http://127.0.0.1:8001/status/{ordem.numero_os}/"
        
        # Cores formais e progresso
        config_status = {
            'RECEBIDO': {'cor': '#475569', 'pct': '15%'},
            'DIAGNOSTICO': {'cor': '#0284c7', 'pct': '35%'},
            'REPARACAO': {'cor': '#2563eb', 'pct': '65%'},
            'AGUARDANDO_PECAS': {'cor': '#d97706', 'pct': '50%'},
            'FINALIZADO': {'cor': '#059669', 'pct': '100%'}
        }
        
        conf = config_status.get(ordem.status, config_status['RECEBIDO'])
        cor_destaque = conf['cor']
        percentagem = conf['pct']

        assunto = f"Notificação de Serviço: {veiculo.placa}"
        from_email = settings.EMAIL_HOST_USER
        
        texto_informativo = mensagem_customizada if mensagem_customizada else "Estimado cliente, informamos que o estado do serviço da sua viatura foi atualizado conforme os detalhes abaixo."

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <style>
                @media only screen and (max-width: 600px) {{
                    .container {{ width: 100% !important; border-radius: 0 !important; }}
                    .content {{ padding: 20px !important; }}
                    .button {{ width: 100% !important; display: block !important; box-sizing: border-box; }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f7fa; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7fa;">
                <tr>
                    <td align="center" style="padding: 20px 10px;">
                        <table class="container" width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                            
                            <tr>
                                <td style="background-color: #ffffff; padding: 30px 40px; border-bottom: 2px solid #f1f5f9; text-align: left;">
                                    <div style="font-size: 20px; font-weight: bold; color: #1e293b; letter-spacing: -0.5px;">GESTOR DE FROTA</div>
                                    <div style="font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase;">Serviços Técnicos Automóveis</div>
                                </td>
                            </tr>

                            <tr>
                                <td class="content" style="padding: 40px;">
                                    <h2 style="color: #1e293b; font-size: 18px; margin-bottom: 20px; font-weight: 600;">Olá, {veiculo.proprietario}</h2>
                                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin-bottom: 30px;">
                                        {texto_informativo}
                                    </p>

                                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 10px;">
                                        <tr>
                                            <td style="font-size: 11px; font-weight: bold; color: #64748b; text-transform: uppercase;">Progresso: {ordem.get_status_display()}</td>
                                            <td style="font-size: 11px; font-weight: bold; color: {cor_destaque}; text-align: right;">{percentagem}</td>
                                        </tr>
                                    </table>
                                    <div style="width: 100%; background-color: #f1f5f9; border-radius: 50px; height: 8px; margin-bottom: 35px;">
                                        <div style="width: {percentagem}; background-color: {cor_destaque}; height: 8px; border-radius: 50px;"></div>
                                    </div>

                                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border-radius: 8px; padding: 20px;">
                                        <tr>
                                            <td style="padding-bottom: 15px; border-bottom: 1px solid #e2e8f0;">
                                                <span style="font-size: 10px; color: #94a3b8; font-weight: bold; text-transform: uppercase; display: block;">Viatura</span>
                                                <span style="font-size: 16px; color: #1e293b; font-weight: bold;">{veiculo.marca} {veiculo.modelo}</span>
                                                <span style="font-size: 14px; color: #64748b; display: block;">{veiculo.placa}</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding-top: 15px;">
                                                <span style="font-size: 10px; color: #94a3b8; font-weight: bold; text-transform: uppercase; display: block;">Estado do Serviço</span>
                                                <span style="font-size: 15px; color: {cor_destaque}; font-weight: bold;">{ordem.get_status_display().upper()}</span>
                                            </td>
                                        </tr>
                                    </table>

                                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 40px;">
                                        <tr>
                                            <td align="center">
                                                <a href="{link_status}" class="button" style="background-color: #1e293b; color: #ffffff; padding: 15px 35px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
                                                    Acompanhar Serviço Online
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <tr>
                                <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                    <p style="color: #94a3b8; font-size: 12px; margin: 0; line-height: 1.5;">
                                        Este e-mail foi gerado automaticamente pelo sistema de gestão.<br>
                                        <strong>© 2026 Oficina Profissional</strong>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(assunto, text_content, from_email, [cliente_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Erro e-mail: {e}")

# --- RESTANTE DAS VIEWS ---

def abrir_detalhe_os(request, os_id):
    request.session['os_id_atual'] = os_id
    return redirect('detalhe_os_sessao')

def detalhe_os(request):
    os_id = request.session.get('os_id_atual')
    if not os_id:
        messages.warning(request, "Nenhuma Ordem de Serviço selecionada.")
        return redirect('dashboard')
    os_instancia = get_object_or_404(OrdemServico, id=os_id)
    return render(request, 'os/detalhe_os.html', {'os': os_instancia})

def dashboard(request):
    fila_espera = OrdemServico.objects.filter(status='RECEBIDO', mecanico__isnull=True).order_by('data_abertura')
    trabalhos_ativos = OrdemServico.objects.filter(status='REPARACAO').order_by('-data_atribuicao')
    os_finalizadas = OrdemServico.objects.filter(status='FINALIZADO', data_atribuicao__isnull=False, data_fechamento__isnull=False)
    
    tempo_medio_oficina = 0
    if os_finalizadas.exists():
        tempos = [(os.data_fechamento - os.data_atribuicao).total_seconds() for os in os_finalizadas]
        tempo_medio_oficina = (sum(tempos) / len(tempos)) / 3600

    return render(request, 'dashboard.html', {
        'fila': fila_espera,
        'trabalhos_ativos': trabalhos_ativos,
        'mecanicos': User.objects.all(),
        'tempo_medio': round(tempo_medio_oficina, 1), 
    })

def atribuir_mecanico(request):
    if request.method == "POST":
        os_id = request.POST.get('os_id')
        mecanico_id = request.POST.get('mecanico_id')
        ordem = get_object_or_404(OrdemServico, id=os_id)
        
        # --- NOVO: CHECK LOGÍSTICO ANTES DE ATRIBUIR ---
        if ordem.status_pecas() == 'vermelho':
            messages.error(request, f"BLOQUEIO: A viatura {ordem.veiculo.placa} não pode iniciar sem as peças em stock!")
            return redirect('dashboard')
            
        ordem.mecanico = get_object_or_404(User, id=mecanico_id)
        ordem.status = 'REPARACAO'
        if not ordem.data_atribuicao:
            ordem.data_atribuicao = timezone.now()
        ordem.save()
        messages.success(request, f"Técnico atribuído!")
        enviar_email_profissional(ordem)
        request.session['os_id_atual'] = ordem.id
        return redirect('detalhe_os_sessao')
    return redirect('dashboard')

def finalizar_os(request):
    os_id = request.session.get('os_id_atual')
    if not os_id: return redirect('dashboard')
    ordem = get_object_or_404(OrdemServico, id=os_id)
    if request.method == "POST":
        for peca in ordem.pecas.all():
            peca.marca = request.POST.get(f'marca_{peca.id}', peca.marca)
            qtd_form = request.POST.get(f'qtd_{peca.id}')
            if qtd_form:
                try: peca.quantidade = Decimal(str(qtd_form).replace(',', '.'))
                except: pass
            peca.confirmado = True if request.POST.get(f'confirmado_{peca.id}') else False
            peca.save()
            
        nova_nome = request.POST.get('nova_peca_nome')
        if nova_nome and nova_nome.strip():
            nova_marca = request.POST.get('nova_peca_marca', '')
            nova_qtd_raw = request.POST.get('nova_peca_qtd', '1')
            try: nova_qtd = Decimal(str(nova_qtd_raw).replace(',', '.'))
            except: nova_qtd = Decimal('1.0')
            PecaOS.objects.create(ordem_servico=ordem, nome_peca=nova_nome.strip(), marca=nova_marca, quantidade=nova_qtd, preco_unitario=0.00)
        
        ordem.diagnostico_tecnico = request.POST.get('diagnostico_tecnico', '')
        horas_raw = request.POST.get('horas_mao_de_obra')
        if horas_raw:
            try: ordem.horas_mao_de_obra = Decimal(str(horas_raw).replace(',', '.'))
            except: pass
            
        if request.POST.get('botao_finalizar') == "true":
            # --- NOVO: ABATER DO STOCK AO FINALIZAR ---
            for p_os in ordem.pecas.all():
                if p_os.peca_referencia:
                    p_stock = p_os.peca_referencia
                    p_stock.quantidade_em_stock -= p_os.quantidade
                    p_stock.save()

            ordem.status = 'FINALIZADO'
            ordem.data_fechamento = timezone.now()
            ordem.save()
            hora_pronto = (timezone.now() + timedelta(minutes=15)).strftime('%H:%M')
            msg_custom = f"Estimado cliente, informamos que a manutenção da sua viatura foi concluída com sucesso. O veículo estará disponível para levantamento em 15 minutos (pelas {hora_pronto}h)."
            enviar_email_profissional(ordem, mensagem_customizada=msg_custom)
            messages.info(request, f"OS Finalizada. Inventário atualizado e cliente notificado.")
            return redirect('dashboard')
            
        ordem.save()
        messages.success(request, "Rascunho guardado.")
        return redirect('detalhe_os_sessao')
    return redirect('dashboard')

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