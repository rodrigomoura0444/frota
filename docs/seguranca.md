---

### 2. `docs/modelos_dados.md` (Engenharia de Software)
```markdown
# 🏗 Modelagem de Dados e Relacionamentos

A integridade referencial é garantida pelo motor de base de dados, utilizando as seguintes entidades principais:

## 📐 Diagrama de Classes (UML)

```mermaid
classDiagram
    class Veiculo {
        +String placa
        +String marca
        +String modelo
        +get_total_gasto()
    }
    class OrdemServico {
        +Int numero_os
        +DateTime data_abertura
        +Decimal valor_pecas
        +Decimal valor_mao_de_obra
        +calcular_total()
    }
    class Cliente {
        +String nome
        +String nif
    }

    Cliente "1" -- "*" Veiculo : possui
    Veiculo "1" -- "*" OrdemServico : histórico