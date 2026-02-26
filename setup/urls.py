from django.contrib import admin
from django.urls import path
from gestao import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('os/', views.lista_os, name='lista_os'),
    
    # Rota que o Dashboard chama
    path('os/abrir/<int:os_id>/', views.abrir_detalhe_os, name='abrir_os_sessao'),
    
    # ROTA CORRIGIDA (Sem espaços e com o nome que a views.py espera)
    path('os/detalhe/', views.detalhe_os, name='detalhe_os_sessao'), 

    # Operações
    path('os/pdf/<int:os_id>/', views.gerar_pdf_os, name='gerar_pdf_os'),
    path('atribuir/', views.atribuir_mecanico, name='atribuir_mecanico'),
    path('os/finalizar/', views.finalizar_os, name='finalizar_os'),
    
    path('clientes/', views.clientes, name='clientes'),
    
    # Acompanhamento público
    path('status/<str:os_numero>/', views.acompanhar_reparacao, name='acompanhar_reparacao'),
]