from django.contrib import admin
from django.urls import path
from gestao import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Página Inicial / Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Ordens de Serviço
    path('os/', views.lista_os, name='lista_os'),
    path('os/<int:pk>/', views.detalhe_os, name='detalhe_os'),
    path('os/pdf/<int:os_id>/', views.gerar_pdf_os, name='gerar_pdf_os'),
    
    # Clientes (Adicionada para resolver o erro NoReverseMatch)
    path('clientes/', views.clientes, name='clientes'),
]