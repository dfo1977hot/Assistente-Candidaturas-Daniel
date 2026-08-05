# Geração de versão estruturada

`GenerateStructuredResumeVersionUseCase` representa a intenção explícita de
gerar uma nova versão estruturada para uma candidatura. A entrada mínima é
`application_id`; a seleção visual de versões, o preview e a versão adotada não
fazem parte da requisição.

O caso de uso reutiliza o fluxo de elegibilidade, o contrato de provider
estruturado e a porta transacional de escrita. Em sucesso, cria uma versão para
revisão. Ele não adota a versão, não muda a origem efetiva do currículo e não
executa avaliação ATS.

O resultado é um contrato Application com status funcional, identificadores
seguros e mensagem. `StructuredResumeGenerationViewModel` converte esse
contrato em estado imutável de Presentation; não conhece provider, banco ou
infraestrutura.
