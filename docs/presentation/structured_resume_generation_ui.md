# Geração estruturada na ApplicationPage

`ApplicationPage` recebe `StructuredResumeGenerationViewModel` por injeção do
composition root. A dependência pode ser ausente apenas em construções legadas;
nesse caso, o botão **Gerar versão estruturada** permanece desabilitado e a
página não resolve nem cria dependências.

A ação é independente de **Otimizar currículo**. Ambas usam o
`LongRunningTaskExecutor` existente e ficam desabilitadas enquanto qualquer
uma das gerações estiver ativa. A requisição contém apenas a candidatura ativa.

O resultado só atualiza a página se seu `application_id` ainda for o contexto
ativo. Sucesso atualiza o histórico para revisão; falhas, resultados obsoletos
e resultados inesperados não adotam versões, não mudam preview ou origem do
currículo e não acionam ATS.
