# Preview do currículo efetivo

`EffectiveApplicationResumePreviewPanel` mostra em modo somente leitura o conteúdo
efetivamente usado pela candidatura. Ele recebe apenas um ViewState e não acessa
casos de uso, contêiner, banco ou infraestrutura.

A `ApplicationPage` atualiza o preview ao carregar outra candidatura e depois de uma
adoção bem-sucedida ou retorno ao currículo original. Alterar apenas a versão
visualizada não atualiza o preview. Em estados indisponíveis, o conteúdo anterior é
limpo e uma mensagem segura é exibida.
