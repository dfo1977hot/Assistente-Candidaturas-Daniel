# Comunicações & Outlook Classic 1.0

## Escopo

Adapter local de leitura do Outlook Classic para o contrato provider-neutral
`MailMessageReader`.

## Regras

- Windows + Outlook Classic.
- Sem OAuth, Microsoft Graph, Gmail ou senha no ACD.
- COM inicializado dentro do worker que executa a sincronização.
- Caixa de Entrada padrão via namespace MAPI.
- Coleção ordenada por `ReceivedTime` decrescente.
- Associação somente por correspondência exata do endereço SMTP do recrutador.
- Para remetentes Exchange (`SenderEmailType == EX`), resolver endereço SMTP real.
- `EntryID` usado como identidade do item dentro do provider `outlook_classic`.
- Somente leitura: não enviar, responder, excluir, mover, salvar ou alterar `UnRead`.
- Timeline e `Data resposta` continuam sob as regras de `CommunicationsService` e Follow-up.
- Falha de COM/Outlook deve produzir mensagem amigável.

## Dependência

`pywin32>=312,<313` somente em Windows.

## Fora de escopo

- Novo Outlook.
- Microsoft Graph.
- envio automático;
- varredura contínua em background;
- Calendar/Teams;
- leitura de corpo ou anexos.

## Gate

1. compileall direcionado;
2. Ruff direcionado;
3. testes Outlook + Communications + Follow-up;
4. execução real do aplicativo;
5. teste manual com Outlook Classic;
6. Ruff global;
7. pytest global.
