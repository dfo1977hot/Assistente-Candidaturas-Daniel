# Contrato de Provider de IA

O contrato único é `acd.infrastructure.ai.providers.AIProvider`.

```python
def generate_text(
    *,
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    language: str,
) -> str: ...
```

## Responsabilidades

- Receber um prompt já montado.
- Produzir uma resposta textual.
- Respeitar os parâmetros explícitos de geração.

## Não responsabilidades

- Montar ou versionar prompts.
- Persistir prompts, gerações ou logs.
- Conhecer páginas, casos de uso ou entidades de UI.
- Fazer seleção automática de provider.

## Implementação disponível

`MockAIProvider` implementa o contrato de forma determinística para testes e
desenvolvimento local. Ele não usa rede nem serviços externos.

Implementações futuras devem satisfazer o mesmo contrato e ser injetadas nos
serviços de geração, sem alterar os casos de uso existentes.
