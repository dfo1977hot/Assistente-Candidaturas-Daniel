# Exportação DOCX na ApplicationPage

O botão **Exportar currículo em DOCX** abre `QFileDialog` com o filtro Word e
normaliza a extensão `.docx`. Cancelar não inicia tarefa. A página recebe o
ViewModel por injeção; sem ele ou sem candidatura, o botão permanece desabilitado.

A tarefa `effective_resume_docx_export` usa o `LongRunningTaskExecutor` já
existente. Durante a execução mostra **Exportando...** e bloqueia os fluxos de
otimização e geração. Resultados e falhas são correlacionados ao `application_id`;
eventos obsoletos não alteram a candidatura atual. Exportar não atualiza preview
ou histórico, nem adota versão ou executa ATS.
