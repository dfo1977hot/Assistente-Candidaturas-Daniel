from __future__ import annotations

import re
from typing import Protocol


class Parser(Protocol):
    """Interface para parsers determinísticos."""

    def parse(self, text: str) -> dict[str, list[str]]: ...


class TextParser:
    """Parser simples baseado em regex e regras."""

    SKILL_CATALOG = {
        "Lean": "metodologia",
        "Six Sigma": "metodologia",
        "Power BI": "tecnologia",
        "Excel": "tecnologia",
        "SAP": "tecnologia",
        "Oracle": "tecnologia",
        "SQL": "tecnologia",
        "Python": "tecnologia",
        "Kanban": "metodologia",
        "PDCA": "metodologia",
        "MRP": "metodologia",
        "S&OP": "metodologia",
        "Kaizen": "metodologia",
    }

    LANGUAGE_PATTERNS = {
        "Inglês": re.compile(r"inglês|english", re.I),
        "Português": re.compile(r"português|portuguese", re.I),
        "Espanhol": re.compile(r"espanhol|spanish", re.I),
    }

    SENIORITY_PATTERNS = {
        "Estágio": re.compile(r"estágio|internship", re.I),
        "Júnior": re.compile(r"júnior|junior", re.I),
        "Pleno": re.compile(r"pleno|mid|senioridade pl|analista", re.I),
        "Sênior": re.compile(r"sênior|senior", re.I),
        "Especialista": re.compile(r"especialista", re.I),
        "Coordenador": re.compile(r"coordenador", re.I),
        "Gerente": re.compile(r"gerente", re.I),
        "Diretor": re.compile(r"diretor", re.I),
    }

    CERTIFICATION_PATTERNS = [
        re.compile(r"green belt", re.I),
        re.compile(r"black belt", re.I),
        re.compile(r"iso 9001", re.I),
        re.compile(r"apqp", re.I),
        re.compile(r"ppap", re.I),
        re.compile(r"lean six sigma", re.I),
    ]

    def parse(self, text: str) -> dict[str, list[str]]:
        lowered = text.lower()
        skills = [skill for skill in self.SKILL_CATALOG if skill.lower() in lowered]
        technologies = [skill for skill in skills if self.SKILL_CATALOG[skill] == "tecnologia"]
        methodologies = [skill for skill in skills if self.SKILL_CATALOG[skill] == "metodologia"]
        languages = [
            name for name in self.LANGUAGE_PATTERNS if self.LANGUAGE_PATTERNS[name].search(text)
        ]
        certifications = [
            match.group(0).strip()
            for pattern in self.CERTIFICATION_PATTERNS
            for match in [pattern.search(text)]
            if match
        ]
        seniority = [
            name for name in self.SENIORITY_PATTERNS if self.SENIORITY_PATTERNS[name].search(text)
        ]
        return {
            "skills": skills,
            "technologies": technologies,
            "methodologies": methodologies,
            "languages": languages,
            "certifications": certifications,
            "seniority": seniority,
        }
