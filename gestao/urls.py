from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('os/', views.lista_os, name='lista_os'),
    path('os/pdf/<int:os_id>/', views.gerar_pdf_os, name='gerar_pdf_os'), # Rota do PDF
]