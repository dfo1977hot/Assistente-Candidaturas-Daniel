from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PromptContext:
    """Contexto estruturado para montar prompts de geração de currículo e carta."""

    vacancy_title: str = ""
    vacancy_description: str = ""
    ats_score: float = 0.0
    missing_skills: list[str] | None = None
    curriculum_summary: str = ""
    professional_history: str = ""
    user_goals: str = ""
    language: str = "pt-BR"
    document_blocks: tuple[str, ...] = ()


class PromptBuilder:
    """Responsável por montar prompts determinísticos para geração de conteúdo."""

    def build_resume_prompt(self, context: PromptContext) -> str:
        """Monta um prompt para otimização de currículo."""
        missing = ", ".join(context.missing_skills or [])
        layout_instructions = self._resume_layout_instructions(context.document_blocks)

        return (
            "Você é um especialista em recrutamento e currículo. "
            f"Crie uma versão otimizada de currículo para a vaga "
            f"'{context.vacancy_title}'. "
            f"Contexto da vaga: {context.vacancy_description}. "
            f"ATS score atual: {context.ats_score}. "
            f"Competências faltantes: {missing or 'nenhuma'}. "
            f"Resumo do currículo atual: {context.curriculum_summary}. "
            f"Histórico profissional: {context.professional_history}. "
            f"Objetivos do usuário: {context.user_goals}. "
            f"Escreva em {context.language} e destaque competências técnicas "
            "e palavras-chave ATS. "
            "Não invente experiências, resultados, qualificações, empresas, "
            "cargos, cursos ou competências que não estejam presentes no "
            "currículo original. "
            f"{layout_instructions}"
        )

    def build_cover_letter_prompt(self, context: PromptContext) -> str:
        """Monta um prompt para geração de carta de apresentação."""
        missing = ", ".join(context.missing_skills or [])
        return (
            "Você é um especialista em recrutamento. "
            f"Escreva uma carta de apresentação personalizada para a vaga "
            f"'{context.vacancy_title}'. "
            f"Contexto da vaga: {context.vacancy_description}. "
            f"ATS score atual: {context.ats_score}. "
            f"Competências faltantes: {missing or 'nenhuma'}. "
            f"Resumo do currículo atual: {context.curriculum_summary}. "
            f"Objetivos do usuário: {context.user_goals}. "
            f"Escreva em {context.language} com tom profissional e persuasivo."
        )

    @staticmethod
    def _resume_layout_instructions(document_blocks: tuple[str, ...]) -> str:
        """Preserva a estrutura do DOCX por meio de blocos posicionais."""
        if not document_blocks:
            return ""

        serialized_blocks = "\n".join(
            f"[[BLOCO {index}]] {text}"
            for index, text in enumerate(document_blocks, start=1)
        )

        return (
            "O currículo original possui uma estrutura visual que deve ser "
            "preservada integralmente. Abaixo estão os blocos textuais do "
            "documento na ordem em que aparecem. "
            "Otimize somente o texto de cada bloco. "
            "Não crie, remova, una, divida ou reordene blocos. "
            "A resposta deve conter exatamente a mesma quantidade de blocos. "
            "Cada bloco da resposta deve começar exatamente com "
            "'[[BLOCO N]]', mantendo a numeração original. "
            "Responda todos os blocos de 1 até o último, sem pular nenhum. "
            "Se um bloco não precisar de melhoria, repita o texto original "
            "desse bloco exatamente sob o mesmo marcador. "
            "Não use cercas de código, listas Markdown, títulos Markdown, "
            "negrito nos marcadores ou qualquer outro invólucro. "
            "Não escreva introdução, conclusão, comentários ou explicações "
            "fora dos blocos. "
            "Preserve dados factuais, nomes de empresas, cargos, períodos e "
            "resultados existentes.\n"
            f"{serialized_blocks}"
        )
