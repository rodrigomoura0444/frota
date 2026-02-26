# Segurança e Integridade de Dados

Uma das camadas mais complexas deste projeto é a proteção contra **ID Enumeration** (quando um utilizador tenta mudar o número na URL para ver dados de outros).

## Ocultação de Parâmetros via Session
Em vez de expor caminhos como `/os/detalhe/55/`, implementámos um padrão de **Ponte de Sessão**:

1. **Ação:** O utilizador clica num link dinâmico.
2. **Ponte:** Uma view intermédia captura o ID e grava-o no `request.session['os_id_atual']`.
3. **Redirecionamento:** O utilizador é enviado para uma URL "limpa" `/os/detalhe/`.
4. **Resgate:** A view final lê o ID da memória do servidor e renderiza os dados.



### Benefícios
* **Segurança:** Oculta a estrutura da base de dados.
* **Limpeza Visual:** URLs elegantes e curtas.
* **Contexto:** Impede acessos diretos sem um fluxo de navegação válido.