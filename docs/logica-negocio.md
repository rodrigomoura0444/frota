# Lógica de Negócio e Auditoria

O Mesh Auto utiliza algoritmos para calcular a eficiência da oficina.

## Monitorização de Estadia (Lead Time)
A eficiência é calculada através da diferença temporal entre os marcos de estado.

### Cálculo de Permanência
A fórmula aplicada para determinar quanto tempo a viatura ocupou o espaço físico da oficina é:

$$Permanência = Data\ de\ Fechamento - Data\ de\ Abertura$$



### Implementação no Django Admin
No `admin.py`, o campo `tempo_permanencia_formatado` utiliza lógica condicional para apresentar dados dinâmicos:
1. **Se Finalizado:** Mostra o tempo total decorrido.
2. **Se em Curso:** Mostra o tempo decorrido desde a entrada até ao momento atual (`timezone.now()`).

### Eficiência Média (Dashboard)
A dashboard calcula a média aritmética de todas as ordens finalizadas, convertendo o `timedelta` em horas flutuantes para análise gerencial de produtividade.