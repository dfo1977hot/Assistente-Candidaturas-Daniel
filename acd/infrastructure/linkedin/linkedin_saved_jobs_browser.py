"""Browser adapter for the authenticated LinkedIn saved-jobs tracker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import logging
from pathlib import Path
import re
import time
from urllib.parse import quote

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)

logger = logging.getLogger(__name__)

TRACKER_URL = "https://www.linkedin.com/jobs-tracker/"
LOGIN_URL = (
    "https://www.linkedin.com/login?fromSignIn=true&session_redirect="
    f"{quote(TRACKER_URL, safe='')}"
)
_NEXT_PAGE_TEXT = re.compile(r"^\s*(?:próxima|proxima|next)\s*$", re.IGNORECASE)
_CLOSED_APPLICATION_MESSAGES = (
    "não aceita mais candidaturas",
    "nao aceita mais candidaturas",
    "candidaturas encerradas",
    "inscrições encerradas",
    "inscricoes encerradas",
    "no longer accepting applications",
    "applications are closed",
    "application closed",
)


class LinkedInSavedJobsBrowserError(RuntimeError):
    """Controlled failure while reading the LinkedIn saved-jobs page."""


@dataclass(frozen=True, slots=True)
class SavedLinkedInJob:
    """Minimal job reference collected from the authenticated tracker."""

    url: str
    linkedin_job_id: str
    title: str = ""
    company_name: str = ""
    location: str = ""
    accepting_applications: bool | None = None
    work_model: str = ""
    employment_type: str = ""
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str = ""
    recruiter_email: str = ""
    application_url: str = ""


class LinkedInSavedJobsBrowser:
    """Read saved jobs through a persistent, user-controlled Chrome profile."""

    def __init__(
        self,
        *,
        profile_directory: Path | None = None,
        login_timeout_seconds: float = 300.0,
        navigation_timeout_ms: int = 60_000,
        maximum_pages: int = 250,
        headless: bool | Callable[[], bool] = False,
    ) -> None:
        self._profile_directory = profile_directory or (
            Path.home() / ".acd" / "linkedin-playwright-profile"
        )
        self._login_timeout_seconds = max(30.0, login_timeout_seconds)
        self._navigation_timeout_ms = max(10_000, navigation_timeout_ms)
        self._maximum_pages = max(1, maximum_pages)
        self._headless = headless

    def _runs_headless(self) -> bool:
        value = self._headless
        return bool(value() if callable(value) else value)

    def collect_saved_jobs(
        self,
        *,
        cancellation_requested: Callable[[], bool] | None = None,
        status_callback: Callable[[str], None] | None = None,
        excluded_job_ids: set[str] | None = None,
        permanently_excluded_job_ids: set[str] | None = None,
    ) -> list[SavedLinkedInJob]:
        """Open LinkedIn, wait for login when needed, and collect unique saved jobs."""
        self._profile_directory.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            runs_headless = self._runs_headless()
            launch_options = {
                "user_data_dir": str(self._profile_directory),
                "headless": runs_headless,
                "viewport": {"width": 1440, "height": 960},
            }
            if not runs_headless:
                launch_options["channel"] = "chrome"

            context = playwright.chromium.launch_persistent_context(
                **launch_options,
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(self._navigation_timeout_ms)
                self._notify(status_callback, "Abrindo o LinkedIn...")
                page.goto(TRACKER_URL, wait_until="domcontentloaded")
                self._wait_for_tracker(
                    page,
                    cancellation_requested=cancellation_requested,
                    status_callback=status_callback,
                )
                references = self._collect_all(
                    page,
                    cancellation_requested=cancellation_requested,
                    status_callback=status_callback,
                )
                excluded = excluded_job_ids or set()
                permanently_excluded = permanently_excluded_job_ids or set()
                new_references = [
                    reference
                    for reference in references
                    if (
                        reference.linkedin_job_id not in permanently_excluded
                        and (
                            reference.linkedin_job_id not in excluded
                            or reference.accepting_applications is False
                        )
                    )
                ]
                skipped = len(references) - len(new_references)
                if skipped:
                    self._notify(
                        status_callback,
                        f"{skipped} vaga(s) já processada(s) ignorada(s).",
                    )
                return self._classify_application_statuses(
                    page,
                    new_references,
                    cancellation_requested=cancellation_requested,
                    status_callback=status_callback,
                )
            finally:
                context.close()

    def _classify_application_statuses(
        self,
        page: Page,
        references: list[SavedLinkedInJob],
        *,
        cancellation_requested: Callable[[], bool] | None,
        status_callback: Callable[[str], None] | None,
    ) -> list[SavedLinkedInJob]:
        """Open every job detail and identify vacancies with closed applications."""
        classified: list[SavedLinkedInJob] = []
        total = len(references)

        for current, reference in enumerate(references, start=1):
            self._raise_if_cancelled(cancellation_requested)
            self._notify(
                status_callback,
                f"Verificando candidaturas {current}/{total}: "
                f"{reference.title or reference.linkedin_job_id}",
            )
            accepting: bool | None = reference.accepting_applications
            work_model = ""
            employment_type = ""
            salary_min: Decimal | None = None
            salary_max: Decimal | None = None
            currency = ""
            recruiter_email = ""
            application_url = ""
            try:
                if accepting is False:
                    classified.append(reference)
                    continue
                page.goto(reference.url, wait_until="domcontentloaded")
                page.wait_for_timeout(1_000)
                body_text = page.locator("body").inner_text(timeout=10_000)
                reports_closed = self._text_reports_closed_applications(body_text)
                work_model = self._extract_work_model(body_text)
                employment_type = self._extract_employment_type(body_text)
                salary_min, salary_max, currency = self._extract_salary(body_text)
                recruiter_email = self._extract_public_email(body_text)

                if not reports_closed:
                    application_url = self._detect_application_url(page, reference.url)

                accepting = not reports_closed
                if application_url and self._same_job_and_application_url(
                    reference.url,
                    application_url,
                ):
                    accepting = False
            except Exception:
                accepting = None

            classified.append(
                SavedLinkedInJob(
                    url=reference.url,
                    linkedin_job_id=reference.linkedin_job_id,
                    title=reference.title,
                    company_name=reference.company_name,
                    location=reference.location,
                    accepting_applications=accepting,
                    work_model=work_model,
                    employment_type=employment_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    recruiter_email=recruiter_email,
                    application_url=application_url,
                )
            )

        return classified

    @classmethod
    def _detect_application_url(cls, page: Page, job_url: str) -> str:
        """Detect the application target while the saved-job page is already open."""
        external = PlaywrightApplicationBrowser._linkedin_external_apply_url(page)
        if not external:
            external = PlaywrightApplicationBrowser._linkedin_external_url_from_frames(
                page
            )
        if not external:
            external = (
                PlaywrightApplicationBrowser._linkedin_external_url_from_page_content(
                    page
                )
            )
        if external:
            return external

        if PlaywrightApplicationBrowser._linkedin_has_easy_apply(page):
            return PlaywrightApplicationBrowser._linkedin_easy_apply_url(
                page,
                job_url,
            )
        return ""

    @staticmethod
    def _same_job_and_application_url(job_url: str, application_url: str) -> bool:
        return job_url.strip().rstrip("/") == application_url.strip().rstrip("/")

    @classmethod
    def _page_reports_closed_applications(cls, page: Page) -> bool:
        body_text = page.locator("body").inner_text(timeout=10_000)
        return cls._text_reports_closed_applications(body_text)

    @staticmethod
    def _text_reports_closed_applications(body_text: str) -> bool:
        normalized = body_text.casefold()
        return any(message in normalized for message in _CLOSED_APPLICATION_MESSAGES)

    @staticmethod
    def _extract_work_model(body_text: str) -> str:
        normalized = body_text.casefold()
        if re.search(r"\b(?:híbrido|hibrido|hybrid)\b", normalized):
            return "Híbrido"
        if re.search(r"\b(?:remoto|remote|home office)\b", normalized):
            return "Remoto"
        if re.search(r"\b(?:presencial|on-site|onsite)\b", normalized):
            return "Presencial"
        return ""

    @staticmethod
    def _extract_employment_type(body_text: str) -> str:
        normalized = body_text.casefold()
        mappings = (
            (r"\b(?:pj|pessoa jurídica|pessoa juridica|contractor|freelance)\b", "PJ"),
            (r"\b(?:temporário|temporario|temporary)\b", "Temporário"),
            (r"\b(?:estágio|estagio|internship|intern)\b", "Estágio"),
            (r"\b(?:aprendiz|apprentice)\b", "Aprendiz"),
            (r"\b(?:clt|tempo integral|full-time|full time)\b", "CLT"),
        )
        for pattern, value in mappings:
            if re.search(pattern, normalized):
                return value
        return ""

    @staticmethod
    def _extract_public_email(body_text: str) -> str:
        """Return a recruiter/RH e-mail explicitly shown in the vacancy text."""

        email_pattern = re.compile(
            r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.-])",
            flags=re.IGNORECASE,
        )
        recruiting_terms = (
            "recrut",
            "recursos humanos",
            "talent",
            "career",
            "vaga",
            "jobs",
            "people",
            "gente",
            "rh",
        )
        blocked_fragments = (
            "linkedin.com",
            "example.com",
            "noreply",
            "no-reply",
            "donotreply",
            "do-not-reply",
        )

        for line in body_text.splitlines():
            for match in email_pattern.finditer(line):
                candidate = match.group(1).strip()
                normalized = candidate.casefold()
                if any(fragment in normalized for fragment in blocked_fragments):
                    continue
                local_part = normalized.split("@", 1)[0]
                context = line.casefold()
                if any(term in context or term in local_part for term in recruiting_terms):
                    return candidate
        return ""

    @classmethod
    def _extract_salary(
        cls,
        body_text: str,
    ) -> tuple[Decimal | None, Decimal | None, str]:
        compact = " ".join(body_text.split())
        patterns = (
            (
                r"R\$\s*([\d.]+(?:,\d{1,2})?)\s*(?:a|até|–|-)"
                r"\s*R?\$?\s*([\d.]+(?:,\d{1,2})?)",
                "BRL",
            ),
            (
                r"(?:US\$|USD|\$)\s*([\d,]+(?:\.\d{1,2})?)"
                r"\s*(?:a|to|–|-)\s*(?:US\$|USD|\$)?\s*"
                r"([\d,]+(?:\.\d{1,2})?)",
                "USD",
            ),
        )
        for pattern, currency in patterns:
            match = re.search(pattern, compact, re.IGNORECASE)
            if not match:
                continue
            minimum = cls._parse_salary_number(match.group(1), currency)
            maximum = cls._parse_salary_number(match.group(2), currency)
            if minimum is not None and maximum is not None:
                return min(minimum, maximum), max(minimum, maximum), currency
        return None, None, ""

    @staticmethod
    def _parse_salary_number(value: str, currency: str) -> Decimal | None:
        normalized = value.strip()
        if currency == "BRL":
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    def _wait_for_tracker(
        self,
        page: Page,
        *,
        cancellation_requested: Callable[[], bool] | None,
        status_callback: Callable[[str], None] | None,
    ) -> None:
        deadline = time.monotonic() + self._login_timeout_seconds
        login_page_opened = False
        last_tracker_retry = 0.0

        while time.monotonic() < deadline:
            self._raise_if_cancelled(cancellation_requested)

            if "/jobs-tracker" in page.url and self._has_job_links(page):
                return

            now = time.monotonic()
            if self._is_not_found_page(page) and not login_page_opened:
                self._notify(
                    status_callback,
                    "Este navegador ainda não está autenticado. Faça login no LinkedIn; "
                    "a importação continuará automaticamente.",
                )
                page.goto(LOGIN_URL, wait_until="domcontentloaded")
                login_page_opened = True
            elif self._is_login_or_checkpoint(page):
                self._notify(
                    status_callback,
                    "Faça login no LinkedIn no navegador aberto. A importação continuará "
                    "automaticamente.",
                )
                login_page_opened = True
            elif now - last_tracker_retry >= 3.0:
                self._notify(status_callback, "Abrindo o Rastreador de vagas...")
                page.goto(TRACKER_URL, wait_until="domcontentloaded")
                last_tracker_retry = now
            else:
                self._notify(status_callback, "Aguardando o carregamento das vagas salvas...")

            page.wait_for_timeout(1_000)

        raise LinkedInSavedJobsBrowserError(
            "O tempo para abrir a página de vagas salvas ou concluir o login foi excedido."
        )

    def _collect_all(
        self,
        page: Page,
        *,
        cancellation_requested: Callable[[], bool] | None,
        status_callback: Callable[[str], None] | None,
    ) -> list[SavedLinkedInJob]:
        collected: dict[str, SavedLinkedInJob] = {}
        visited_pages: set[tuple[str, ...]] = set()

        for page_number in range(1, self._maximum_pages + 1):
            self._raise_if_cancelled(cancellation_requested)
            current_page_jobs = self._collect_current_page(
                page,
                cancellation_requested=cancellation_requested,
            )
            signature = self._jobs_signature(current_page_jobs)
            if signature and signature in visited_pages:
                break
            if signature:
                visited_pages.add(signature)

            for job in current_page_jobs:
                collected.setdefault(job.linkedin_job_id or job.url, job)

            self._notify(
                status_callback,
                f"Página {page_number}: {len(collected)} vaga(s) salva(s) encontrada(s)...",
            )

            if not self._advance_to_next_page(
                page,
                current_signature=signature,
                cancellation_requested=cancellation_requested,
            ):
                break
        else:
            self._notify(
                status_callback,
                "O limite de páginas foi alcançado; revise se todas as vagas foram coletadas.",
            )

        if not collected:
            raise LinkedInSavedJobsBrowserError(
                "Nenhuma vaga salva foi encontrada. Confirme que a página está aberta "
                "na seção de vagas salvas e que há vagas disponíveis."
            )
        return list(collected.values())

    def _collect_current_page(
        self,
        page: Page,
        *,
        cancellation_requested: Callable[[], bool] | None,
    ) -> list[SavedLinkedInJob]:
        """Collect every card loaded on the current tracker page without changing pages."""
        jobs: dict[str, SavedLinkedInJob] = {}
        unchanged_rounds = 0

        for _ in range(12):
            self._raise_if_cancelled(cancellation_requested)
            before = len(jobs)
            for job in self._extract_visible_jobs(page):
                jobs.setdefault(job.linkedin_job_id or job.url, job)

            unchanged_rounds = unchanged_rounds + 1 if len(jobs) == before else 0
            if unchanged_rounds >= 2:
                break

            page.mouse.wheel(0, 1_800)
            page.wait_for_timeout(350)

        return list(jobs.values())

    def _advance_to_next_page(
        self,
        page: Page,
        *,
        current_signature: tuple[str, ...],
        cancellation_requested: Callable[[], bool] | None,
    ) -> bool:
        """Click the enabled Next/Próxima control and wait for tracker content to change."""
        control = self._find_next_control(page)
        if control is None:
            return False

        old_active_page = self._active_page_text(page)
        try:
            control.scroll_into_view_if_needed(timeout=2_000)
            control.click(timeout=5_000)
        except PlaywrightTimeoutError:
            return False

        deadline = time.monotonic() + min(20.0, self._navigation_timeout_ms / 1_000)
        while time.monotonic() < deadline:
            self._raise_if_cancelled(cancellation_requested)
            page.wait_for_timeout(250)
            new_signature = self._visible_signature(page)
            new_active_page = self._active_page_text(page)
            if new_signature and new_signature != current_signature:
                return True
            if old_active_page and new_active_page and new_active_page != old_active_page:
                return True

        return False

    @staticmethod
    def _has_job_links(page: Page) -> bool:
        return page.locator('a[href*="/jobs/view/"], a[href*="currentJobId="]').count() > 0

    @staticmethod
    def _is_login_or_checkpoint(page: Page) -> bool:
        return "/login" in page.url or "/checkpoint/" in page.url

    @staticmethod
    def _is_not_found_page(page: Page) -> bool:
        body_text = page.locator("body").inner_text(timeout=5_000).casefold()
        return "página não encontrada" in body_text or "page not found" in body_text

    def _extract_visible_jobs(self, page: Page) -> list[SavedLinkedInJob]:
        jobs: list[SavedLinkedInJob] = []
        anchors = page.locator('a[href*="/jobs/view/"], a[href*="currentJobId="]')
        for index in range(anchors.count()):
            anchor = anchors.nth(index)
            href = anchor.get_attribute("href") or ""
            job_id = self._job_id(href)
            if not job_id:
                continue
            title = (anchor.get_attribute("aria-label") or anchor.inner_text() or "").strip()
            container = anchor.locator(
                "xpath=ancestor::*[self::li or @data-job-id or contains(@class,'job-card')][1]"
            )
            text = container.inner_text().strip() if container.count() else ""
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            company = lines[1] if len(lines) > 1 else ""
            location = lines[2] if len(lines) > 2 else ""
            accepting_applications = (
                False if self._text_reports_closed_applications(text) else None
            )
            jobs.append(
                SavedLinkedInJob(
                    url=self._canonical_url(job_id),
                    linkedin_job_id=job_id,
                    title=title,
                    company_name=company,
                    location=location,
                    accepting_applications=accepting_applications,
                )
            )
        return jobs

    def _find_next_control(self, page: Page):
        selectors = (
            'button[aria-label*="Next" i]',
            'button[aria-label*="Próxima" i]',
            'button[aria-label*="Proxima" i]',
            'a[aria-label*="Next" i]',
            'a[aria-label*="Próxima" i]',
            'a[aria-label*="Proxima" i]',
        )
        for selector in selectors:
            candidate = self._first_enabled_visible(page.locator(selector))
            if candidate is not None:
                return candidate

        text_candidates = page.locator("button, a").filter(has_text=_NEXT_PAGE_TEXT)
        return self._first_enabled_visible(text_candidates)

    @staticmethod
    def _first_enabled_visible(locator):
        for index in range(locator.count()):
            candidate = locator.nth(index)
            if not candidate.is_visible():
                continue
            aria_disabled = (candidate.get_attribute("aria-disabled") or "").casefold()
            class_name = (candidate.get_attribute("class") or "").casefold()
            if aria_disabled == "true" or "disabled" in class_name:
                continue
            try:
                if not candidate.is_enabled():
                    continue
            except Exception as error:
                logger.debug(
                    "Could not inspect enabled state for LinkedIn pagination control",
                    exc_info=error,
                )
            return candidate
        return None

    @staticmethod
    def _active_page_text(page: Page) -> str:
        selectors = (
            '[aria-current="page"]',
            'button[aria-pressed="true"]',
            '.active',
        )
        for selector in selectors:
            locator = page.locator(selector)
            for index in range(locator.count()):
                text = (locator.nth(index).inner_text() or "").strip()
                if text.isdigit():
                    return text
        return ""

    def _visible_signature(self, page: Page) -> tuple[str, ...]:
        return self._jobs_signature(self._extract_visible_jobs(page))

    @staticmethod
    def _jobs_signature(jobs: list[SavedLinkedInJob]) -> tuple[str, ...]:
        return tuple(sorted({job.linkedin_job_id or job.url for job in jobs}))

    @staticmethod
    def _job_id(url: str) -> str:
        match = re.search(r"(?:currentJobId=|/jobs/view/(?:[^/?]+-)?)(\d{6,})", url)
        return match.group(1) if match else ""

    @staticmethod
    def _canonical_url(job_id: str) -> str:
        return f"https://www.linkedin.com/jobs/view/{job_id}/"

    @staticmethod
    def _notify(callback: Callable[[str], None] | None, message: str) -> None:
        if callback is not None:
            callback(message)

    @staticmethod
    def _raise_if_cancelled(callback: Callable[[], bool] | None) -> None:
        if callback is not None and callback():
            raise LinkedInSavedJobsBrowserError("Importação cancelada pelo usuário.")
