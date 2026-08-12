# Codex Task — Cartas 1.1

## Objetivo
Evoluir a página Cartas adicionando barra de progresso real em `Gerar com IA`, execução não bloqueante, cancelamento cooperativo e reforço de versionamento/UX, preservando a arquitetura e as regras atuais do ACD.

## Antes de alterar código
1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Inspecione o worktree atual.
4. Inspecione `letter_page.py`, `CoverLetterService`, Composition Root e o executor de tarefas longas já existente.
5. Use o worktree local validado como fonte de verdade.

## Regras que não podem regredir
- Cada nova geração cria nova versão.
- Nunca sobrescrever versão anterior.
- IA não pode inventar experiências, resultados, cargos, competências ou números.
- Carta permanece vinculável a Vaga, Currículo e Candidatura.
- Presentation não importa Infrastructure.
- Presentation não instancia Service/Repository.
- Dependências concretas são criadas no Composition Root.
- Gupy permanece manual-only.
- `Salário esperado = Remuneração ideal`.
- `Data resposta` permanece vazia sem resposta real.

## Escopo

### Barra de progresso
Adicionar barra visível na página Cartas. Atualizar por fases reais:
- Preparando contexto
- Carregando vaga
- Carregando currículo
- Montando prompt
- Gerando conteúdo
- Validando resposta
- Salvando nova versão
- Concluído

Não usar timer para simular progresso.

### Execução não bloqueante
A geração não deve congelar a UI. Reutilize o executor/threading já existente no ACD. Durante a geração, desabilite ações conflitantes e mantenha `Cancelar` disponível.

### Cancelamento
Implementar cancelamento cooperativo.
- Antes da persistência: não criar versão.
- Depois de persistir: não apagar silenciosamente uma versão válida.
- Restaurar controles e informar o usuário.

### Contexto
Usar somente dados reais disponíveis:
- vaga;
- empresa;
- cargo;
- recrutador/e-mail quando existentes;
- descrição/notas da vaga;
- currículo selecionado;
- candidatura relacionada quando houver;
- competências/resultados realmente existentes no ACD.

Bloquear geração se faltar Vaga ou Currículo. Se faltar conteúdo suficiente da vaga, avisar; não inventar requisitos.

### Versionamento
Preservar V1.0 → V1.1 → V1.2...
`Regenerar` sempre cria nova versão.
Adicionar teste para múltiplas gerações consecutivas.

### Estado do registro
Após Gerar, Salvar, Exportar DOCX ou Exportar PDF, permanecer no mesmo registro. Não limpar formulário automaticamente.

### Exportação
Preservar DOCX/PDF. Nome de arquivo seguro; erro de I/O deve gerar mensagem amigável; exportar não altera versão.

### Copiar
Copiar conteúdo atual sem alterar banco e exibir confirmação discreta.

### Status
Preservar: Rascunho, Gerada, Revisada, Aprovada, Enviada, Arquivada.
Após geração bem-sucedida, usar `Gerada` salvo regra existente mais específica. Nunca marcar automaticamente como `Enviada`.

### Integração Workflows 1.1
Página Cartas e handler `generate_cover_letter` devem reutilizar o mesmo `CoverLetterService`. Não criar caminho paralelo.

## Testes obrigatórios
1. barra de progresso existe;
2. geração não bloqueia UI;
3. controles conflitantes desabilitados durante geração;
4. Cancelar permanece disponível;
5. cancelamento antes de persistir não cria versão;
6. sucesso chega a 100%;
7. falha restaura controles;
8. múltiplas gerações criam versões distintas;
9. prompt não instrui inventar experiências;
10. falta de vaga bloqueia;
11. falta de currículo bloqueia;
12. mesmo registro permanece após gerar;
13. mesmo registro permanece após salvar;
14. exportação não muda versão;
15. Workflow e Cartas reutilizam `CoverLetterService`;
16. Presentation não importa Infrastructure;
17. Presentation não instancia Service/Repository.

## Gates
Execute testes direcionados e depois obrigatoriamente:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não faça commit se qualquer gate estiver vermelho.

## Entrega
Responder com:
1. arquivos alterados;
2. arquitetura implementada;
3. comportamento da barra de progresso;
4. comportamento do cancelamento;
5. versionamento preservado;
6. testes direcionados;
7. Ruff global;
8. pytest global;
9. `APPROVED` ou `BLOCKED`.

## Não fazer
- progresso fake por timer;
- bloquear thread principal;
- sobrescrever carta;
- inventar fatos profissionais;
- duplicar `CoverLetterService`;
- Presentation -> Infrastructure;
- automatizar Gupy;
- commitar antes dos gates globais verdes.
