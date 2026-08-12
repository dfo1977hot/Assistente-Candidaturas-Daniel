# Codex Task — Acompanhamento de Candidaturas & Follow-up 1.0

## Objetivo
Criar uma camada operacional de acompanhamento de candidaturas integrada ao ACD, usando dados reais de Candidaturas, Workflows, Dashboard e histórico de interações, sem duplicar regras de negócio.

## Antes de alterar código
1. Leia `AGENTS.md`.
2. Leia `.github/CONSTITUTION.md`.
3. Leia `docs/codex/workflows-2.0.md`.
4. Leia `docs/codex/dashboard-analytics-1.0.md`.
5. Leia `docs/codex/dashboard-analytics-1.1.md`.
6. Inspecione o worktree atual e use-o como fonte de verdade.

## Regras arquiteturais
- Presentation não importa Infrastructure.
- Presentation não instancia Service/Repository.
- Regras de acompanhamento ficam em Services/Domain.
- Workflows permanece apenas orquestrador.
- Não duplicar regras de Candidaturas.
- Não automatizar envio de e-mail ou mensagem sem ação explícita do usuário.
- Não inventar contatos, e-mails, datas ou respostas.
- Gupy permanece manual-only.
- `Salário esperado = Remuneração ideal`.
- `Data resposta` só é preenchida quando houver resposta real.

## Escopo funcional

### 1. Estado de acompanhamento
Adicionar/reutilizar no domínio/serviço:
- próxima ação;
- data prevista de follow-up;
- última interação;
- tipo da última interação;
- observação de acompanhamento;
- prioridade;
- indicador `follow_up_required`.

Evitar nova coluna/tabela quando o modelo atual já suportar o dado adequadamente; se migração for necessária, fazê-la de forma compatível.

### 2. Tipos de interação
Suportar registro manual de:
- candidatura enviada;
- e-mail enviado;
- mensagem LinkedIn enviada;
- ligação realizada;
- retorno recebido;
- entrevista agendada;
- entrevista realizada;
- feedback recebido;
- proposta recebida;
- rejeição;
- outro.

Não marcar automaticamente como enviado/recebido sem evento real.

### 3. Timeline da candidatura
Adicionar visão cronológica por candidatura com data/hora, tipo, resumo, origem e referências relacionadas quando existirem.

### 4. Próxima ação
Permitir definir ação, data, horário opcional, prioridade e observação.

Ações iniciais:
- Enviar follow-up;
- Verificar status;
- Preparar entrevista;
- Atualizar candidatura;
- Revisar vaga;
- Aguardar retorno;
- Outro.

### 5. ApplicationFollowUpService
Responsabilidades:
- calcular candidaturas que exigem atenção;
- identificar follow-ups vencidos;
- identificar candidaturas sem atualização;
- calcular próxima ação;
- registrar interação;
- concluir/adiar follow-up;
- fornecer DTOs para Dashboard/Workflows.

Não enviar mensagens automaticamente.

### 6. Integração com Workflows
Conectar, quando seguro:
- `review_application`
- `check_follow_up`

Criar/ajustar template `Acompanhamento de candidatura`.

`classify_closed_job` permanece fora de escopo se não houver evidência segura.

### 7. Dashboard
Integrar ao bloco `Atenção necessária`:
- follow-ups vencidos;
- candidaturas sem atualização;
- entrevistas próximas;
- aguardando usuário.

Reutilizar o drill-down do Dashboard 1.1.

### 8. UI Candidaturas
Adicionar seção compacta:
- Próxima ação;
- Data do follow-up;
- Prioridade;
- Última interação;
- Registrar interação;
- Concluir/adiar follow-up;
- Ver timeline.

Preservar o layout existente.

### 9. Integração com Cartas
Permitir registrar manualmente que carta vinculada foi utilizada/enviada.
Não marcar carta como `Enviada` só por gerar/exportar.

### 10. Integração futura com Gmail
Preparar boundaries para futura leitura/registro de respostas, mas NÃO implementar Gmail nesta Sprint.

## Testes obrigatórios
1. criar próxima ação;
2. follow-up vencido;
3. follow-up futuro;
4. concluir follow-up;
5. adiar follow-up;
6. registrar interação;
7. timeline cronológica;
8. timeline não inventa eventos;
9. Data resposta vazia sem resposta real;
10. retorno real pode preencher Data resposta;
11. prioridade preservada;
12. candidatura sem atualização gera atenção;
13. entrevista próxima gera atenção;
14. `review_application` usa Service real;
15. `check_follow_up` usa Service real;
16. workflow com follow-up vencido entra em `Aguardando usuário`;
17. workflow sem follow-up vencido não cria ação falsa;
18. Dashboard mostra follow-ups vencidos;
19. drill-down preserva filtros;
20. UI permanece no mesmo registro;
21. Presentation não importa Infrastructure;
22. Presentation não instancia Service/Repository;
23. Composition Root injeta `ApplicationFollowUpService`;
24. nenhuma regressão Workflows 2.0;
25. nenhuma regressão Dashboard 1.1;
26. nenhuma regressão Cartas 1.1;
27. regras salariais preservadas;
28. Gupy manual-only.

## Gates obrigatórios
Execute testes direcionados primeiro.

Depois:

`C:\Projetos\.venv\Scripts\python.exe -m ruff check .`

`C:\Projetos\.venv\Scripts\python.exe -m pytest -q`

Não faça commit enquanto qualquer gate estiver vermelho.

## Entrega esperada
1. arquivos alterados;
2. arquitetura implementada;
3. campos/regras de acompanhamento;
4. timeline;
5. integrações com Workflows e Dashboard;
6. testes direcionados;
7. Ruff global;
8. pytest global;
9. pendências;
10. `APPROVED` ou `BLOCKED`.

## Não fazer
- não enviar e-mail/mensagem automaticamente;
- não inventar contato ou resposta;
- não preencher Data resposta sem evento real;
- não automatizar Gupy;
- não duplicar lógica;
- não colocar SQL em Presentation;
- não enfraquecer arquitetura;
- não commitar antes dos gates verdes.
