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


class PromptBuilder:
    """Responsável por montar prompts determinísticos para geração de conteúdo."""

    def build_resume_prompt(self, context: PromptContext) -> str:
        """Monta um prompt para otimização de currículo."""
        missing = ", ".join(context.missing_skills or [])
        return (
            f"Você é um especialista em recrutamento e currículo. "
            f"Crie uma versão otimizada de currículo para a vaga '{context.vacancy_title}'. "
            f"Contexto da vaga: {context.vacancy_description}. "
            f"ATS score atual: {context.ats_score}. "
            f"Competências faltantes: {missing or 'nenhuma'}. "
            f"Resumo do currículo atual: {context.curriculum_summary}. "
            f"Histórico profissional: {context.professional_history}. "
            f"Objetivos do usuário: {context.user_goals}. "
            f"Escreva em {context.language} e destaque competências técnicas e palavras-chave ATS."
        )

    def build_cover_letter_prompt(self, context: PromptContext) -> str:
        """Monta um prompt para geração de carta de apresentação."""
        missing = ", ".join(context.missing_skills or [])
        return (
            f"Você é um especialista em recrutamento. "
            f"Escreva uma carta de apresentação personalizada para a vaga '{context.vacancy_title}'. "
            f"Contexto da vaga: {context.vacancy_description}. "
            f"ATS score atual: {context.ats_score}. "
            f"Competências faltantes: {missing or 'nenhuma'}. "
            f"Resumo do currículo atual: {context.curriculum_summary}. "
            f"Objetivos do usuário: {context.user_goals}. "
            f"Escreva em {context.language} com tom profissional e persuasivo."
        )
