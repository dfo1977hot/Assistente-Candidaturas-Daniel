# Currículo efetivo da candidatura

O currículo efetivo é resolvido exclusivamente a partir da candidatura persistida:
`resume_source`, `selected_resume_version_id` e `curriculum_id`.

`EffectiveApplicationResumeUseCase` é somente leitura. Para `ORIGINAL`, retorna o
conteúdo textual do currículo associado. Para `RESUME_VERSION`, procura a versão
adotada somente entre as versões do mesmo `curriculum_id`.

Não há fallback silencioso: uma seleção inconsistente, uma versão ausente ou conteúdo
indisponível retorna um status funcional e nenhum conteúdo. A versão visualizada, a
mais recente e resultados ATS não participam da resolução. O caso de uso não altera
currículos, versões, candidaturas ou persistência.
