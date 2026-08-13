from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from typing import Any, Protocol

from acd.core.datetime_utils import utc_now


class ApplicationFollowUpRepository(Protocol):
    def get_by_id(self, application_id: int) -> Any | None: ...
    def get_all(self) -> list[Any]: ...
    def update(self, application: Any) -> Any: ...
    def get_followups(self, application_id: int) -> list[Any]: ...
    def add_event(
        self,
        application_id: int,
        event_type: str,
        description: str,
        **metadata: object,
    ) -> Any: ...


@dataclass(frozen=True)
class FollowUpState:
    application_id: int
    next_action: str
    follow_up_date: date | None
    follow_up_time: str
    priority: str
    note: str
    last_interaction_at: datetime | None
    last_interaction_type: str
    follow_up_required: bool
    attention_reasons: tuple[str, ...]


@dataclass(frozen=True)
class TimelineItem:
    id: int
    occurred_at: datetime
    interaction_type: str
    summary: str
    origin: str
    reference_type: str
    reference_id: int | None


class ApplicationFollowUpService:
    """Manage explicit follow-up state without sending or inventing interactions."""

    INTERACTION_TYPES = (
        "Candidatura enviada",
        "E-mail enviado",
        "Mensagem LinkedIn enviada",
        "Ligação realizada",
        "Retorno recebido",
        "Entrevista agendada",
        "Entrevista realizada",
        "Feedback recebido",
        "Proposta recebida",
        "Rejeição",
        "Outro",
    )
    REAL_RESPONSE_TYPES = frozenset(
        {"Retorno recebido", "Feedback recebido", "Proposta recebida", "Rejeição"}
    )
    ACTION_TYPES = (
        "Enviar follow-up",
        "Verificar status",
        "Preparar entrevista",
        "Atualizar candidatura",
        "Revisar vaga",
        "Aguardar retorno",
        "Outro",
    )
    PRIORITIES = ("Baixa", "Normal", "Alta", "Urgente")
    TERMINAL_STATUSES = frozenset({"Contratada", "Rejeitada", "Encerrada"})
    STALE_DAYS = 14
    UPCOMING_INTERVIEW_DAYS = 7

    def __init__(self, repository: ApplicationFollowUpRepository) -> None:
        self.repository = repository

    def set_next_action(
        self,
        application_id: int,
        *,
        action: str,
        follow_up_date: date | None,
        follow_up_time: str = "",
        priority: str = "Normal",
        note: str = "",
    ) -> FollowUpState:
        if action not in self.ACTION_TYPES:
            raise ValueError("Ação de acompanhamento inválida.")
        if priority not in self.PRIORITIES:
            raise ValueError("Prioridade de acompanhamento inválida.")
        if follow_up_time and not self._valid_time(follow_up_time):
            raise ValueError("Horário deve usar o formato HH:MM.")
        application = self._application(application_id)
        clean_note = note.strip()
        if (
            getattr(application, "next_action", "") == action
            and application.next_follow_up == follow_up_date
            and getattr(application, "follow_up_time", "") == follow_up_time
            and getattr(application, "follow_up_priority", "Normal") == priority
            and getattr(application, "follow_up_note", "") == clean_note
        ):
            return self.get_state(application_id)
        application.next_action = action
        application.next_follow_up = follow_up_date
        application.follow_up_time = follow_up_time
        application.follow_up_priority = priority
        application.follow_up_note = clean_note
        application.last_update = date.today()
        self.repository.update(application)
        self.repository.add_event(
            application_id,
            "Próxima ação definida",
            self._action_summary(action, follow_up_date, follow_up_time),
            origin="manual",
        )
        return self.get_state(application_id)

    def register_interaction(
        self,
        application_id: int,
        *,
        interaction_type: str,
        summary: str,
        occurred_at: datetime | None = None,
        origin: str = "manual",
        reference_type: str = "",
        reference_id: int | None = None,
    ) -> TimelineItem:
        if interaction_type not in self.INTERACTION_TYPES:
            raise ValueError("Tipo de interação inválido.")
        if not summary.strip():
            raise ValueError("Informe um resumo da interação real.")
        application = self._application(application_id)
        timestamp = occurred_at or utc_now()
        event = self.repository.add_event(
            application_id,
            interaction_type,
            summary.strip(),
            origin=origin,
            reference_type=reference_type,
            reference_id=reference_id,
            created_at=timestamp,
        )
        application.last_update = timestamp.date()
        if interaction_type in self.REAL_RESPONSE_TYPES and application.response_date is None:
            application.response_date = timestamp.date()
        self.repository.update(application)
        return self._timeline_item(event, occurred_at=timestamp)

    def register_letter_usage(
        self, application_id: int, letter_id: int, *, summary: str = "Carta utilizada"
    ) -> TimelineItem:
        return self.register_interaction(
            application_id,
            interaction_type="Outro",
            summary=summary,
            reference_type="cover_letter",
            reference_id=letter_id,
        )

    def complete_follow_up(self, application_id: int, *, note: str = "") -> FollowUpState:
        application = self._application(application_id)
        previous_action = application.next_action or "Follow-up"
        application.next_action = ""
        application.next_follow_up = None
        application.follow_up_time = ""
        application.follow_up_note = ""
        application.last_update = date.today()
        self.repository.update(application)
        description = f"{previous_action} concluído"
        if note.strip():
            description += f": {note.strip()}"
        self.repository.add_event(
            application_id, "Follow-up concluído", description, origin="manual"
        )
        return self.get_state(application_id)

    def postpone_follow_up(
        self, application_id: int, new_date: date, *, note: str = ""
    ) -> FollowUpState:
        application = self._application(application_id)
        if not application.next_action:
            raise ValueError("Defina uma próxima ação antes de adiar o follow-up.")
        application.next_follow_up = new_date
        if note.strip():
            application.follow_up_note = note.strip()
        application.last_update = date.today()
        self.repository.update(application)
        self.repository.add_event(
            application_id,
            "Follow-up adiado",
            f"Follow-up adiado para {new_date.isoformat()}",
            origin="manual",
        )
        return self.get_state(application_id)

    def get_timeline(self, application_id: int) -> tuple[TimelineItem, ...]:
        self._application(application_id)
        events = self._chronological_events(application_id)
        return tuple(self._timeline_item(event) for event in events)

    def get_state(self, application_id: int, *, today: date | None = None) -> FollowUpState:
        application = self._application(application_id)
        events = self._chronological_events(application_id)
        current = today or date.today()
        reasons = self._attention_reasons(application, current)
        interactions = [event for event in events if event.event_type in self.INTERACTION_TYPES]
        last = interactions[-1] if interactions else None
        return FollowUpState(
            application_id=application.id,
            next_action=getattr(application, "next_action", "") or "",
            follow_up_date=application.next_follow_up,
            follow_up_time=getattr(application, "follow_up_time", "") or "",
            priority=getattr(application, "follow_up_priority", "Normal") or "Normal",
            note=getattr(application, "follow_up_note", "") or "",
            last_interaction_at=getattr(last, "created_at", None),
            last_interaction_type=getattr(last, "event_type", "") if last else "",
            follow_up_required=bool(reasons),
            attention_reasons=tuple(reasons),
        )

    def list_requiring_attention(self, *, today: date | None = None) -> tuple[FollowUpState, ...]:
        current = today or date.today()
        states = [self.get_state(item.id, today=current) for item in self.repository.get_all()]
        return tuple(state for state in states if state.follow_up_required)

    def is_overdue(self, application_id: int, *, today: date | None = None) -> bool:
        state = self.get_state(application_id, today=today)
        return state.follow_up_date is not None and state.follow_up_date < (today or date.today())

    def _attention_reasons(self, application: Any, current: date) -> list[str]:
        if application.status in self.TERMINAL_STATUSES:
            return []
        reasons = []
        if application.next_follow_up and application.next_follow_up < current:
            reasons.append("follow_up_overdue")
        updated_at = getattr(application, "updated_at", None)
        last_update = application.last_update or (
            updated_at.date() if updated_at is not None else current
        )
        if last_update < current - timedelta(days=self.STALE_DAYS):
            reasons.append("stale_application")
        if application.interview_date and current <= application.interview_date <= (
            current + timedelta(days=self.UPCOMING_INTERVIEW_DAYS)
        ):
            reasons.append("upcoming_interview")
        return reasons

    def _application(self, application_id: int) -> Any:
        application = self.repository.get_by_id(application_id)
        if application is None:
            raise ValueError("Candidatura não localizada.")
        return application

    def _chronological_events(self, application_id: int) -> list[Any]:
        return sorted(
            self.repository.get_followups(application_id),
            key=lambda event: (event.created_at, event.id),
        )

    @staticmethod
    def _valid_time(value: str) -> bool:
        if re.fullmatch(r"\d{2}:\d{2}", value) is None:
            return False
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            return False
        return True

    @staticmethod
    def _action_summary(action: str, follow_up_date: date | None, follow_up_time: str) -> str:
        when = follow_up_date.isoformat() if follow_up_date else "sem data"
        if follow_up_time:
            when += f" às {follow_up_time}"
        return f"{action}: {when}"

    @staticmethod
    def _timeline_item(event: Any, *, occurred_at: datetime | None = None) -> TimelineItem:
        return TimelineItem(
            id=int(getattr(event, "id", 0) or 0),
            occurred_at=occurred_at or event.created_at,
            interaction_type=str(event.event_type),
            summary=str(event.description),
            origin=str(getattr(event, "origin", "manual") or "manual"),
            reference_type=str(getattr(event, "reference_type", "") or ""),
            reference_id=getattr(event, "reference_id", None),
        )
