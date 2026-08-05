# Resume Version Review UI

`ResumeVersionReviewPanel` é um componente passivo da `ApplicationPage`. Ele recebe somente `ResumeVersionReviewViewState` pelo `ResumeVersionReviewViewModel` injetado no composition root.

O título é **Versões deste currículo**. O painel mostra, em modo somente leitura, o conteúdo original, a versão selecionada, o seletor de versões persistidas e a explicação já armazenada, quando disponível. A troca no seletor apenas solicita uma nova projeção visual ao ViewModel.

O painel não acessa container, Infrastructure, Query Port, IA ou ATS; não executa geração e não grava dados.
