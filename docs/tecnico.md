# Componentes de Engenharia

## Geração de PDF Dinâmico
Utilizamos a biblioteca `xhtml2pdf` para transformar templates Django em documentos PDF profissionais.
* **Memory Efficiency:** O PDF é gerado num buffer `BytesIO`, evitando escrita em disco e aumentando a velocidade de resposta.
* **Link Callbacks:** Implementámos uma função de callback para que o gerador de PDF consiga localizar ficheiros estáticos (logos/CSS) no servidor.

## Notificações via E-mail (MIME)
O sistema de e-mail não envia apenas texto plano. Utilizamos `EmailMultiAlternatives` para enviar:
1. **Versão HTML:** Um template premium com botões e cores de estado (Verde para finalizado, Azul para reparação).
2. **Versão Texto:** Para compatibilidade com dispositivos antigos.

## Django Admin Inlines
Para otimizar a gestão, as peças utilizadas (`PecaOS`) são editadas diretamente dentro da página da Ordem de Serviço através de `TabularInline`, reduzindo o número de cliques necessários para o administrador.