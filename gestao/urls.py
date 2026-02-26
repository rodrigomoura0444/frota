from django.contrib import admin
from django.urls import path
from gestao import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('os/', views.lista_os, name='lista_os'),
    
    # Rota que recebe o clique do Dashboard
    path('os/abrir/<int:os_id>/', views.abrir_detalhe_os, name='abrir_os_sessao'),
    
    # Mudamos o nome para 'os_trabalho' para forçar o Django a reconhecer a rota
    path('os/detalhe/', views.detalhe_os, name='os_trabalho'), 

    # Operações
    path('os/pdf/<int:os_id>/', views.gerar_pdf_os, name='gerar_pdf_os'),
    path('atribuir/', views.atribuir_mecanico, name='atribuir_mecanico'),
    path('os/finalizar/', views.finalizar_os, name='finalizar_os'),
    
    path('clientes/', views.clientes, name='clientes'),
    path('status/<str:os_numero>/', views.acompanhar_reparacao, name='acompanhar_reparacao'),
]