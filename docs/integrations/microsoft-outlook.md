# Microsoft Outlook / Microsoft Graph — configuração do ACD

A integração de e-mail do ACD usa Microsoft Graph com OAuth 2.0 delegado e MSAL para Python.
O ACD não solicita nem armazena a senha da conta Microsoft e não usa client secret.

## Registro do aplicativo

No Microsoft Entra admin center:

1. Registre um novo aplicativo para o ACD.
2. Selecione o tipo de conta que inclua contas Microsoft pessoais e contas organizacionais, se desejar usar ambos.
3. Em Authentication, adicione a plataforma **Mobile and desktop applications**.
4. Configure o redirect URI `http://localhost`.
5. Habilite o aplicativo como public client quando solicitado pela configuração de desktop.
6. Em API permissions, adicione Microsoft Graph > Delegated permissions > `Mail.ReadBasic`.
7. Não crie client secret para o ACD desktop.

## Configuração no ACD

Em **Configurações > Cofre de Logins**, crie:

- Serviço: `Microsoft Graph`
- URL: pode ficar vazia
- Usuário/E-mail: cole o **Application (client) ID**
- Senha: deixe vazia
- Observações: opcional

O Client ID não é segredo. O cache de tokens OAuth é armazenado pelo ACD no cofre do sistema
operacional por meio do keyring.

Alternativamente, o Client ID pode ser fornecido pela variável de ambiente
`MICROSOFT_GRAPH_CLIENT_ID`.

## Uso

Na página **Candidaturas**:

1. Clique em **Conectar Outlook** e conclua o login no navegador.
2. Selecione uma candidatura que tenha o e-mail do recrutador.
3. Clique em **Sincronizar Outlook**.

A sincronização é somente leitura. A versão 1.0 não envia, responde, exclui, move ou marca
mensagens como lidas. Somente remetente, assunto, data/hora e identificador da mensagem são
usados para associar uma resposta real à timeline da candidatura.
