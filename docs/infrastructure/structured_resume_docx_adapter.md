# Adapter DOCX de currículo estruturado

`PythonDocxStructuredResumeExportAdapter` usa `python-docx` 1.2.0 para renderizar
um `StructuredResumeSnapshot` validado em estrutura linear, com estilos de nome
e títulos, metadados básicos, Unicode e listas reais.

O documento é salvo primeiro em arquivo temporário no mesmo diretório e só então
substitui o destino. Em falha, o temporário é removido; não há parsing textual,
rede ou acesso a banco no adapter.
