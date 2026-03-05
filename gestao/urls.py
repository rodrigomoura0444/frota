# URLs da aplicação gestao
# Mapeamento de URLs para as views
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from gestao import views

# Lista de rotas disponíveis
urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Lista de ordens de serviço
    path('os/', views.lista_os, name='lista_os'),
    
    # Abre detalhe de uma OS específica
    path('os/abrir/<int:os_id>/', views.abrir_detalhe_os, name='abrir_os_sessao'),
    
    # Detalhe da OS (página de trabalho)
    path('os/detalhe/', views.detalhe_os, name='os_trabalho'), 

    # Gera PDF da OS
    path('os/pdf/<int:os_id>/', views.gerar_pdf_os, name='gerar_pdf_os'),
    
    # Atribui mecânico a uma OS
    path('atribuir/', views.atribuir_mecanico, name='atribuir_mecanico'),
    
    # Finaliza uma OS
    path('os/finalizar/', views.finalizar_os, name='finalizar_os'),
    
    # Lista de clientes/veículos
    path('clientes/', views.clientes, name='clientes'),
    
    # Página pública de acompanhamento (acessível ao cliente)
    path('status/<str:os_numero>/', views.acompanhar_reparacao, name='acompanhar_reparacao'),
]
