"""Playwright adapter for assisted, never unattended, job applications."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from html import unescape
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen
import webbrowser

from acd.infrastructure.email.terra_imap_gupy_magic_link_service import (
    TerraImapGupyMagicLinkService,
)
from acd.services.assisted_application_service import (
    ApplicantProfile,
    AssistedApplicationResult,
)
from acd.services.chrome_profile_service import ChromeProfileService
from acd.services.linkedin_application_resolver import LinkedInApplicationResolution
from acd.services.settings_service import SettingsService


class GupyApplicationStage(StrEnum):
    """Known stages in the authenticated Gupy application workflow."""

    WELCOME = "welcome"
    ADDITIONAL_DATA = "additional_data"
    COMPANY_QUESTIONS = "company_questions"
    PRESENTATION = "presentation"
    REVIEW = "review"
    FINAL_SUBMISSION = "final_submission"
    UNKNOWN = "unknown"


class PlaywrightApplicationBrowser:
    """Open and prefill supported forms, leaving final submission to the user."""

    def __init__(
        self,
        magic_link_service: TerraImapGupyMagicLinkService | None = None,
        *,
        settings_service: SettingsService | None = None,
        linkedin_headless: bool | Callable[[], bool] = False,
    ) -> None:
        self.settings_service = settings_service or SettingsService()
        self.magic_link_service = (
            magic_link_service
            or TerraImapGupyMagicLinkService(self.settings_service)
        )
        self._linkedin_headless = linkedin_headless

    def _linkedin_runs_headless(self) -> bool:
        value = self._linkedin_headless
        return bool(value() if callable(value) else value)

    def has_email_credential(self, email_address: str) -> bool:
        return self.magic_link_service.has_credential(email_address)

    def save_email_credential(self, email_address: str, password: str) -> None:
        self.magic_link_service.save_credential(email_address, password)

    _PROFILE_DIR = ChromeProfileService.PROFILE_DIR

    def prepare(
        self,
        *,
        url: str,
        source_url: str | None = None,
        profile: ApplicantProfile,
        resume_path: Path | None,
        progress: Callable[[object], None],
    ) -> AssistedApplicationResult:
        host = urlparse(url).netloc.lower()
        platform = self._platform(host)
        linkedin = "linkedin.com" in host
        source_opened = False

        if source_url and source_url != url:
            progress((20, "Abrindo a página da vaga no navegador padrão"))
            source_opened = self._open_default_browser(source_url)

        if linkedin:
            progress((30, "Abrindo o LinkedIn no navegador padrão"))
            if not self._open_default_browser(url):
                raise RuntimeError(
                    "Não foi possível abrir o LinkedIn no navegador padrão."
                )
            progress((100, "LinkedIn aberto para revisão manual"))
            return AssistedApplicationResult(
                platform=platform,
                url=url,
                fields_filled=0,
                resume_attached=False,
                linkedin_restricted_mode=True,
                source_url_opened=source_opened,
            )

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:  # pragma: no cover - dependency is runtime-only
            raise RuntimeError(
                "Playwright não está instalado no ambiente do aplicativo."
            ) from error

        self._PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(self._PROFILE_DIR.resolve()),
                channel="chrome",
                headless=False,
                viewport={"width": 1366, "height": 900},
                args=["--start-maximized"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            platform = self._platform_after_navigation(page, platform)
            progress((35, f"Abrindo candidatura na {platform}"))

            if platform == "Gupy":
                page = self._prepare_gupy(page, profile, progress)
                fields_filled = 0
                resume_attached = False
                progress((
                    82,
                    "Gupy autenticada; preencha manualmente as etapas restantes",
                ))
            else:
                progress((55, "Identificando e preenchendo campos visíveis"))
                fields_filled = self._fill_profile(page, profile)
                resume_attached = self._attach_resume(page, resume_path)
                progress((
                    80,
                    "Currículo anexado"
                    if resume_attached
                    else "Currículo aguardando anexo",
                ))

            progress((90, "Revise as etapas restantes no navegador; depois feche a janela"))
            while context.pages:
                try:
                    page.wait_for_timeout(500)
                except Exception:
                    break
            progress((100, "Revisão no navegador concluída"))

        return AssistedApplicationResult(
            platform=platform,
            url=url,
            fields_filled=fields_filled,
            resume_attached=resume_attached,
            linkedin_restricted_mode=False,
            source_url_opened=source_opened,
        )

    def resolve_linkedin_application_url(
        self,
        job_url: str,
        progress: Callable[[object], None] | None = None,
    ) -> LinkedInApplicationResolution:
        """Locate the LinkedIn application action without opening its destination."""
        callback = progress or (lambda _value: None)
        callback((10, "Abrindo a vaga do LinkedIn"))

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:  # pragma: no cover - runtime dependency
            raise RuntimeError(
                "Playwright não está instalado no ambiente do aplicativo."
            ) from error

        self._PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(self._PROFILE_DIR.resolve()),
                channel="chrome",
                headless=self._linkedin_runs_headless(),
                viewport={"width": 1366, "height": 900},
                args=[] if self._linkedin_runs_headless() else ["--start-maximized"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(job_url, wait_until="domcontentloaded", timeout=60_000)
            try:
                page.wait_for_timeout(2_000)
            except Exception:
                ...
            callback((45, "Localizando Candidatar-se ou Candidatura simplificada"))

            external_url = self._linkedin_external_apply_url(page)
            if not external_url:
                external_url = self._linkedin_external_url_from_frames(page)
            if not external_url:
                external_url = self._linkedin_external_url_from_page_content(page)
            if not external_url:
                external_url = self._linkedin_external_url_from_context_request(
                    context,
                    job_url,
                )
            if not external_url:
                external_url = self._linkedin_external_url_from_public_html(job_url)

            if external_url:
                callback((100, "Link Candidatar-se localizado"))
                context.close()
                return LinkedInApplicationResolution(
                    url=external_url,
                    application_type="external",
                    accepting_applications=True,
                )

            if self._linkedin_has_easy_apply(page):
                callback((100, "Candidatura simplificada localizada"))
                easy_apply_url = self._linkedin_easy_apply_url(page, job_url)
                context.close()
                return LinkedInApplicationResolution(
                    url=easy_apply_url,
                    application_type="easy_apply",
                    accepting_applications=True,
                )

            # Never classify a vacancy as closed merely because LinkedIn hid the
            # destination URL behind JavaScript. If an Apply control exists, the
            # vacancy is still accepting applications.
            if self._linkedin_has_external_apply_control(page):
                callback((100, "Candidatar-se localizado; URL não pôde ser resolvida"))
                context.close()
                return LinkedInApplicationResolution(
                    application_type="external_unresolved",
                    accepting_applications=True,
                )

            closed = self._linkedin_applications_closed(page)
            context.close()
            if closed:
                callback((100, "Não aceita mais candidaturas"))
                return LinkedInApplicationResolution(
                    application_type="closed_explicit",
                    accepting_applications=False,
                )

            callback((100, "Não foi possível confirmar a forma de candidatura"))
            return LinkedInApplicationResolution(
                application_type="unknown",
                accepting_applications=None,
            )

    @classmethod
    def _linkedin_external_apply_url(cls, page: object) -> str:
        """Resolve external Apply targets, including LinkedIn safety/go redirects."""
        page_url = str(getattr(page, "url", "") or "")

        # 1) First scan every visible/hidden anchor href. LinkedIn frequently renders
        # the external target as linkedin.com/safety/go/?url=<encoded external URL>.
        try:
            anchors = page.locator("a[href]")
            for index in range(anchors.count()):
                anchor = anchors.nth(index) if hasattr(anchors, "nth") else anchors.first
                href = (anchor.get_attribute("href") or "").strip()
                if not href:
                    continue

                absolute_href = urljoin(page_url, href)
                parsed = urlparse(absolute_href)
                is_linkedin_safety_redirect = (
                    "linkedin.com" in parsed.netloc.lower()
                    and parsed.path.rstrip("/").endswith("/safety/go")
                )
                if is_linkedin_safety_redirect:
                    resolved = cls._normalize_external_application_url(
                        absolute_href,
                        page_url,
                    )
                    if resolved:
                        return resolved
        except Exception:
            ...
        # 2) Then inspect controls whose semantics indicate Apply.
        selectors = (
            'a[data-tracking-control-name*="apply-link-offsite"]',
            'a[data-tracking-control-name*="public_jobs_apply"]',
            '[data-tracking-control-name*="apply-link-offsite"]',
            'a[href]:has-text("Candidatar-se")',
            'a[href]:has-text("Candidate-se")',
            'a[href]:has-text("Apply")',
            'button:has-text("Candidatar-se")',
            'button:has-text("Candidate-se")',
            'button:has-text("Apply")',
            '[aria-label*="Candidatar-se"]',
            '[aria-label*="Candidate-se"]',
            '[aria-label*="Apply"]',
        )

        candidates: list[object] = []
        for selector in selectors:
            try:
                locator = page.locator(selector)
                for index in range(locator.count()):
                    candidate = (
                        locator.nth(index) if hasattr(locator, "nth") else locator.first
                    )
                    candidates.append(candidate)

                    for attribute in (
                        "href",
                        "data-href",
                        "data-url",
                        "data-apply-url",
                        "data-redirect-url",
                    ):
                        value = (candidate.get_attribute(attribute) or "").strip()
                        resolved = cls._normalize_external_application_url(
                            value,
                            page_url,
                        )
                        if resolved:
                            return resolved

                    try:
                        ancestor_href = str(
                            candidate.evaluate(
                                "el => (el.closest('a') && el.closest('a').href) || ''"
                            )
                            or ""
                        )
                    except Exception:
                        ancestor_href = ""
                    resolved = cls._normalize_external_application_url(
                        ancestor_href,
                        page_url,
                    )
                    if resolved:
                        return resolved
            except Exception:
                continue

        # 3) Last resort: click only inside the isolated Playwright profile and
        # capture a popup/same-tab navigation. The destination is NOT opened in
        # the user's default browser.
        for candidate in candidates:
            try:
                context = page.context
                original_page_url = str(getattr(page, "url", "") or "")
                original_pages = list(context.pages)

                try:
                    candidate.scroll_into_view_if_needed(timeout=3_000)
                except Exception:
                    ...
                try:
                    candidate.click(timeout=5_000, no_wait_after=True)
                except TypeError:
                    candidate.click()
                except Exception:
                    try:
                        candidate.evaluate("el => el.click()")
                    except Exception:
                        continue

                for _ in range(24):
                    try:
                        page.wait_for_timeout(250)
                    except Exception:
                        break

                    for opened_page in list(context.pages):
                        if opened_page not in original_pages:
                            candidate_url = str(getattr(opened_page, "url", "") or "")
                            resolved = cls._normalize_external_application_url(
                                candidate_url,
                                original_page_url,
                            )
                            if resolved:
                                return resolved

                    candidate_url = str(getattr(page, "url", "") or "")
                    if candidate_url != original_page_url:
                        resolved = cls._normalize_external_application_url(
                            candidate_url,
                            original_page_url,
                        )
                        if resolved:
                            return resolved
            except Exception:
                continue
        return ""

    @classmethod
    def _linkedin_external_url_from_frames(cls, page: object) -> str:
        """Scan the main document and every frame for Apply hrefs and markup."""
        try:
            frames = list(page.frames)
        except Exception:
            frames = []

        if not frames:
            frames = [page]

        page_url = str(getattr(page, "url", "") or "")
        for frame in frames:
            try:
                values = frame.evaluate(
                    """
                    () => {
                        const values = [];
                        const nodes = document.querySelectorAll(
                            'a[href], [data-href], [data-url], '
                            + '[data-apply-url], [data-redirect-url]'
                        );
                        for (const node of nodes) {
                            for (const attr of [
                                'href',
                                'data-href',
                                'data-url',
                                'data-apply-url',
                                'data-redirect-url'
                            ]) {
                                const value = node.getAttribute(attr);
                                if (value) values.push(value);
                            }
                            const text = (
                                node.innerText
                                || node.textContent
                                || node.getAttribute('aria-label')
                                || ''
                            ).trim();
                            if (
                                /candidatar-se|candidate-se|easy apply|candidatura simplificada/i
                                .test(text)
                            ) {
                                values.push(node.outerHTML || '');
                            }
                        }
                        return values;
                    }
                    """
                )
            except Exception:
                continue

            for value in values or []:
                text = str(value or "")
                resolved = cls._normalize_external_application_url(
                    text,
                    page_url,
                )
                if resolved:
                    return resolved
                resolved = cls._extract_external_application_url_from_text(
                    text,
                    page_url,
                )
                if resolved:
                    return resolved
        return ""

    @classmethod
    def _linkedin_external_url_from_context_request(
        cls,
        context: object,
        job_url: str,
    ) -> str:
        """Fetch LinkedIn HTML using the same BrowserContext cookies."""
        try:
            response = context.request.get(
                job_url,
                headers={
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                    "Referer": "https://www.linkedin.com/jobs/",
                },
                timeout=20_000,
            )
            if not response.ok:
                return ""
            html = response.text()
        except Exception:
            return ""

        return cls._extract_external_application_url_from_text(html, job_url)

    @classmethod
    def _linkedin_external_url_from_page_content(cls, page: object) -> str:
        """Search raw DOM/HTML for LinkedIn safety/go and off-site apply URLs."""
        try:
            content = str(page.content() or "")
        except Exception:
            content = ""

        if not content:
            return ""

        page_url = str(getattr(page, "url", "") or "")
        return cls._extract_external_application_url_from_text(content, page_url)

    @classmethod
    def _linkedin_external_url_from_public_html(cls, job_url: str) -> str:
        """Fetch public job HTML as a fallback when the Playwright DOM is limited."""
        request = Request(
            job_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/142.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except Exception:
            return ""

        try:
            html = raw.decode("utf-8", errors="replace")
        except Exception:
            return ""
        return cls._extract_external_application_url_from_text(html, job_url)

    @classmethod
    def _extract_external_application_url_from_text(
        cls,
        text: str,
        base_url: str = "",
    ) -> str:
        """Extract external Apply URLs embedded in HTML, JSON or escaped markup."""
        if not text:
            return ""

        normalized = unescape(text)
        variants = (
            normalized,
            normalized.replace("\\\\u0026", "&")
            .replace("\\\\/", "/")
            .replace("&amp;", "&"),
        )

        markers = (
            "https://www.linkedin.com/safety/go/?",
            "https://linkedin.com/safety/go/?",
            "https:\\/\\/www.linkedin.com\\/safety\\/go\\/?",
            "https:\\/\\/linkedin.com\\/safety\\/go\\/?",
            "/safety/go/?",
            "\\/safety\\/go\\/?",
        )
        terminators = ('"', "'", "<", ">", " ", "\\n", "\\r", "\\t")

        for variant in variants:
            for marker in markers:
                search_from = 0
                search_limit = len(variant)
                while search_from < search_limit:
                    index = variant.find(marker, search_from)
                    if index < 0:
                        break

                    end = len(variant)
                    for terminator in terminators:
                        pos = variant.find(terminator, index)
                        if pos >= 0:
                            end = min(end, pos)

                    wrapped = variant[index:end].rstrip("\\")
                    wrapped = wrapped.replace("\\/", "/")
                    if wrapped.startswith("/"):
                        wrapped = urljoin(base_url, wrapped)

                    resolved = cls._normalize_external_application_url(
                        wrapped,
                        base_url,
                    )
                    if resolved:
                        return resolved

                    search_from = index + len(marker)

        # Common LinkedIn JSON attributes can contain an already-decoded URL.
        keys = (
            '"companyApplyUrl":"',
            '"externalApplyUrl":"',
            '"applyUrl":"',
            '"applyMethod":{"companyApplyUrl":"',
        )
        for variant in variants:
            for key in keys:
                start = 0
                search_limit = len(variant)
                while start < search_limit:
                    index = variant.find(key, start)
                    if index < 0:
                        break
                    value_start = index + len(key)
                    value_end = variant.find('"', value_start)
                    if value_end < 0:
                        break
                    value = variant[value_start:value_end].replace("\\\\/", "/")
                    resolved = cls._normalize_external_application_url(
                        value,
                        base_url,
                    )
                    if resolved:
                        return resolved
                    start = value_end + 1

        return ""

    @classmethod
    def _normalize_external_application_url(
        cls,
        value: str,
        base_url: str = "",
    ) -> str:
        candidate = (value or "").strip()
        if not candidate:
            return ""

        if base_url:
            candidate = urljoin(base_url, candidate)

        # Unwrap LinkedIn redirect/tracking links. Their query commonly contains
        # the real destination (for example vagas.com.br) percent-encoded.
        for _ in range(3):
            parsed = urlparse(candidate)
            if parsed.scheme in {"http", "https"} and (
                "linkedin.com" not in parsed.netloc.lower()
            ):
                return candidate

            query = parse_qs(parsed.query, keep_blank_values=False)
            nested = ""
            for key in (
                "url",
                "dest",
                "destination",
                "redirect",
                "redirect_url",
                "redirectUrl",
                "target",
                "externalUrl",
                "external_url",
                "applyUrl",
                "apply_url",
            ):
                values = query.get(key)
                if values:
                    # parse_qs already percent-decodes query values once. Do not
                    # call unquote() again or legacy encodings such as %e7/%e3
                    # may be corrupted.
                    nested = str(values[0] or "").strip()
                    break
            if not nested or nested == candidate:
                break
            candidate = nested

        return ""

    @staticmethod
    def _linkedin_has_external_apply_control(page: object) -> bool:
        selectors = (
            'a:has-text("Candidatar-se")',
            'button:has-text("Candidatar-se")',
            'a:has-text("Candidate-se")',
            'button:has-text("Candidate-se")',
            'a:has-text("Apply")',
            'button:has-text("Apply")',
            '[aria-label*="Candidatar-se"]',
            '[aria-label*="Candidate-se"]',
            '[aria-label*="Apply"]',
        )
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() and locator.first.is_visible():
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def _linkedin_easy_apply_url(cls, page: object, job_url: str) -> str:
        """Return the most complete LinkedIn URL for Easy Apply."""
        selectors = (
            'a[href]:has-text("Candidatura simplificada")',
            'a[href]:has-text("Easy Apply")',
            '[aria-label*="Candidatura simplificada"]',
            '[aria-label*="Easy Apply"]',
        )

        for selector in selectors:
            try:
                locator = page.locator(selector)
                for index in range(locator.count()):
                    candidate = (
                        locator.nth(index) if hasattr(locator, "nth") else locator.first
                    )
                    href = (candidate.get_attribute("href") or "").strip()
                    if href:
                        absolute = urljoin(
                            str(getattr(page, "url", "") or job_url),
                            href,
                        )
                        if cls._same_linkedin_job(absolute, job_url):
                            return absolute

                    try:
                        ancestor_href = str(
                            candidate.evaluate(
                                "el => (el.closest('a') && el.closest('a').href) || ''"
                            )
                            or ""
                        ).strip()
                    except Exception:
                        ancestor_href = ""
                    if ancestor_href and cls._same_linkedin_job(
                        ancestor_href,
                        job_url,
                    ):
                        return ancestor_href
            except Exception:
                continue

        current_url = str(getattr(page, "url", "") or "").strip()
        if current_url and cls._same_linkedin_job(current_url, job_url):
            return current_url

        return job_url

    @staticmethod
    def _same_linkedin_job(candidate_url: str, job_url: str) -> bool:
        candidate = urlparse(candidate_url)
        expected = urlparse(job_url)

        if "linkedin.com" not in candidate.netloc.lower():
            return False
        if "linkedin.com" not in expected.netloc.lower():
            return False

        def _job_id(parsed: object) -> str:
            parts = [part for part in parsed.path.split("/") if part]
            for index, part in enumerate(parts):
                if part == "view" and index + 1 < len(parts):
                    return parts[index + 1]
            return ""

        return bool(_job_id(candidate)) and _job_id(candidate) == _job_id(expected)

    @staticmethod
    def _linkedin_has_easy_apply(page: object) -> bool:
        selectors = (
            'button:has-text("Candidatura simplificada")',
            'a:has-text("Candidatura simplificada")',
            'button:has-text("Easy Apply")',
            'a:has-text("Easy Apply")',
            '[aria-label*="Candidatura simplificada"]',
            '[aria-label*="Easy Apply"]',
        )
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() and locator.first.is_visible():
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def _linkedin_applications_closed(page: object) -> bool:
        phrases = (
            "Não aceita mais candidaturas",
            "Não estamos mais aceitando candidaturas",
            "Candidaturas encerradas",
            "No longer accepting applications",
            "Applications are closed",
        )
        try:
            body_text = str(page.locator("body").inner_text() or "").casefold()
        except Exception:
            return False
        return any(phrase.casefold() in body_text for phrase in phrases)

    @classmethod
    def _is_external_application_url(cls, url: str) -> bool:
        return bool(cls._normalize_external_application_url(url))

    def _platform_after_navigation(
        self,
        page: object,
        fallback: str,
    ) -> str:
        """Resolve the platform after redirects or popups opened by the vacancy."""
        try:
            pages = list(page.context.pages)
        except Exception:
            pages = [page]

        if page not in pages:
            pages.append(page)

        for candidate in reversed(pages):
            try:
                candidate_url = str(candidate.url or "")
            except Exception:
                continue

            provider = self.settings_service.login_provider_registry.identify(
                candidate_url
            )
            if provider is not None:
                return provider.display_name

            host = urlparse(candidate_url).netloc.lower()
            detected = self._platform(host)
            if detected and detected != host:
                return detected

        return fallback

    @staticmethod
    def _gupy_auth_surface(page: object) -> object:
        """Return the page/frame that contains Gupy passwordless controls."""
        candidates: list[object] = [page]
        try:
            candidates.extend(list(page.frames))
        except Exception:
            ...

        seen: set[int] = set()
        for candidate in candidates:
            identity = id(candidate)
            if identity in seen:
                continue
            seen.add(identity)

            try:
                passwordless = candidate.locator(
                    '#passwordlessSignin, '
                    'button[aria-label="Entrar sem senha"], '
                    'button:has-text("Entrar sem senha")'
                )
                if passwordless.count():
                    return candidate
            except Exception:
                ...

            try:
                current_url = str(getattr(candidate, "url", "") or "").lower()
            except Exception:
                current_url = ""
            if "/candidates/passwordless-signin" in current_url:
                return candidate

            try:
                email = candidate.locator(
                    'input[type="email"], '
                    'input[name*="email" i], '
                    'input[id*="email" i], '
                    'input[name*="cpf" i], '
                    'input[id*="cpf" i]'
                )
                password = candidate.locator('input[type="password"]')
                if email.count() and not password.count():
                    return candidate
            except Exception:
                ...

        return page


    @classmethod
    def _gupy_page_has_visible_password_field(
        cls,
        page: object,
    ) -> bool:
        surface = cls._gupy_auth_surface(page)

        try:
            locator = surface.locator('input[type="password"]')
            return bool(locator.count() and locator.first.is_visible())
        except Exception:
            return False

    @staticmethod
    def _gupy_application_page_is_ready(page: object) -> bool:
        """Return True when the candidate is already inside a usable application."""
        try:
            current_url = str(getattr(page, "url", "") or "").lower()
        except Exception:
            return False

        is_job_apply = (
            "/candidates/jobs/" in current_url and "/apply" in current_url
        )
        is_authenticated_application = "/candidates/applications/" in current_url
        if not (is_job_apply or is_authenticated_application):
            return False

        selectors = (
            'input[type="file"]',
            'form input:not([type="hidden"])',
            "form textarea",
            "form select",
        )
        for selector in selectors:
            try:
                locator = page.locator(selector)
                for index in range(locator.count()):
                    candidate = (
                        locator.nth(index)
                        if hasattr(locator, "nth")
                        else locator.first
                    )
                    if candidate.is_visible():
                        return True
            except Exception:
                continue

        return False

    @classmethod
    def _gupy_page_is_authentication_page(cls, page: object) -> bool:
        try:
            current_url = str(getattr(page, "url", "") or "").lower()
        except Exception:
            current_url = ""

        if any(
            route in current_url
            for route in (
                "/candidates/signin",
                "/candidates/passwordless-signin",
            )
        ):
            return True

        if cls._gupy_page_has_visible_password_field(page):
            return True

        surface = cls._gupy_auth_surface(page)
        try:
            passwordless = surface.locator(
                '#passwordlessSignin, button[aria-label="Entrar sem senha"]'
            )
            if passwordless.count() and passwordless.first.is_visible():
                return True
        except Exception:
            ...

        return False

    @classmethod
    def _ensure_gupy_authentication_page(
        cls,
        page: object,
    ) -> tuple[object, str]:
        """Move to Gupy sign-in only when authentication is actually required."""
        try:
            application_url = str(getattr(page, "url", "") or "")
        except Exception:
            application_url = ""

        if cls._gupy_application_page_is_ready(page):
            return page, application_url

        if cls._gupy_page_is_authentication_page(page):
            return page, application_url

        parsed = urlparse(application_url)
        host = parsed.netloc.lower()

        if (
            parsed.scheme != "https"
            or not host
            or not (host == "gupy.io" or host.endswith(".gupy.io"))
        ):
            raise RuntimeError(
                "Não foi possível determinar uma URL segura de autenticação da Gupy."
            )

        signin_url = f"{parsed.scheme}://{parsed.netloc}/candidates/signin"
        page.goto(
            signin_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        try:
            page.wait_for_timeout(750)
        except Exception:
            ...

        return page, application_url

    @classmethod
    def _return_to_gupy_application(
        cls,
        page: object,
        application_url: str,
    ) -> object:
        """Return to the vacancy and open the authenticated application form."""
        if not application_url:
            return page

        parsed = urlparse(application_url)
        host = parsed.netloc.lower()
        if (
            parsed.scheme != "https"
            or not (host == "gupy.io" or host.endswith(".gupy.io"))
        ):
            return page

        # A magic link may leave another controlled tab already inside the
        # authenticated application. Prefer it instead of navigating that tab
        # back to the public vacancy.
        ready = cls._resolve_ready_gupy_application_page(page)
        if ready is not None:
            return ready

        candidate_apply_url = cls._gupy_candidate_apply_url(application_url)
        if candidate_apply_url:
            try:
                page.goto(
                    candidate_apply_url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )
                try:
                    page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=8_000,
                    )
                except Exception:
                    ...
                ready = cls._wait_for_ready_gupy_application_page(
                    page,
                    timeout_ms=4_000,
                )
                if ready is not None:
                    return ready
            except Exception:
                ...

        try:
            current_url = str(getattr(page, "url", "") or "")
        except Exception:
            current_url = ""

        if current_url != application_url:
            page.goto(
                application_url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

        try:
            page.wait_for_load_state("domcontentloaded", timeout=8_000)
        except Exception:
            ...

        return cls._open_gupy_application_after_authentication(page)

    @staticmethod
    def _gupy_candidate_apply_url(application_url: str) -> str:
        """Build the authenticated candidate URL for a public Gupy job."""
        parsed = urlparse(application_url)
        host = parsed.netloc.lower()
        if (
            parsed.scheme != "https"
            or not (host == "gupy.io" or host.endswith(".gupy.io"))
        ):
            return ""

        match = re.fullmatch(r"/jobs/(\d+)/?", parsed.path)
        if match is None:
            return ""

        job_id = match.group(1)
        return (
            f"{parsed.scheme}://{parsed.netloc}"
            f"/candidates/jobs/{job_id}/apply"
        )

    @classmethod
    def _resolve_ready_gupy_application_page(
        cls,
        page: object,
    ) -> object | None:
        """Find a controlled tab that is already inside the application."""
        try:
            pages = list(page.context.pages)
        except Exception:
            pages = [page]

        if page not in pages:
            pages.append(page)

        for candidate in reversed(pages):
            if cls._gupy_application_page_is_ready(candidate):
                try:
                    candidate.bring_to_front()
                except Exception:
                    ...
                return candidate
        return None

    @classmethod
    def _wait_for_ready_gupy_application_page(
        cls,
        page: object,
        *,
        timeout_ms: int = 8_000,
    ) -> object | None:
        """Wait briefly for a controlled Gupy application page to become usable."""
        elapsed = 0
        interval_ms = 200

        while elapsed < timeout_ms:
            ready = cls._resolve_ready_gupy_application_page(page)
            if ready is not None:
                return ready

            try:
                page.wait_for_timeout(interval_ms)
            except Exception:
                time.sleep(interval_ms / 1_000)
            elapsed += interval_ms

        return cls._resolve_ready_gupy_application_page(page)

    @classmethod
    def _gupy_candidate_href_from_public_job(
        cls,
        page: object,
    ) -> str:
        """Find a candidate/apply href rendered by the public vacancy."""
        try:
            base_url = str(getattr(page, "url", "") or "")
            anchors = page.locator("a[href]")
        except Exception:
            return ""

        for index in range(anchors.count()):
            try:
                anchor = (
                    anchors.nth(index)
                    if hasattr(anchors, "nth")
                    else anchors.first
                )
                href = str(anchor.get_attribute("href") or "").strip()
            except Exception:
                continue

            if not href:
                continue

            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if not cls._gupy_candidate_host(absolute):
                continue

            path = parsed.path.lower()
            if (
                "/candidates/applications/" in path
                or (
                    "/candidates/jobs/" in path
                    and "/apply" in path
                )
            ):
                return absolute

        return ""

    @classmethod
    def _open_gupy_application_after_authentication(
        cls,
        page: object,
    ) -> object:
        cls._dismiss_common_banners(page)

        ready = cls._resolve_ready_gupy_application_page(page)
        if ready is not None:
            return ready

        # Gupy tenants may render the candidate destination directly in an
        # anchor before the visible call-to-action is hydrated. Prefer that
        # deterministic destination when available.
        href_deadline = time.monotonic() + 4.0
        while time.monotonic() < href_deadline:
            candidate_href = cls._gupy_candidate_href_from_public_job(page)
            if candidate_href:
                try:
                    page.goto(
                        candidate_href,
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                except Exception:
                    break

                ready = cls._wait_for_ready_gupy_application_page(
                    page,
                    timeout_ms=5_000,
                )
                if ready is not None:
                    return ready
                break

            try:
                page.wait_for_timeout(200)
            except Exception:
                break

        try:
            context = page.context
        except Exception:
            context = None

        apply_controls = (
            ("button", "Candidatar-se"),
            ("link", "Candidatar-se"),
            ("button", "Candidate-se"),
            ("link", "Candidate-se"),
            ("button", "Inscreva-se"),
            ("link", "Inscreva-se"),
            ("button", "Quero me candidatar"),
            ("link", "Quero me candidatar"),
            ("button", "Aplicar"),
            ("link", "Aplicar"),
            ("button", "Continuar candidatura"),
            ("link", "Continuar candidatura"),
        )

        controls_deadline = time.monotonic() + 8.0
        while time.monotonic() < controls_deadline:
            for role, label in apply_controls:
                try:
                    locator = page.get_by_role(
                        role,
                        name=label,
                        exact=False,
                    )
                except Exception:
                    continue

                for index in range(locator.count()):
                    candidate = (
                        locator.nth(index)
                        if hasattr(locator, "nth")
                        else locator.first
                    )
                    try:
                        if not candidate.is_visible():
                            continue
                    except Exception:
                        continue

                    try:
                        candidate.scroll_into_view_if_needed(timeout=3_000)
                    except Exception:
                        ...

                    try:
                        candidate.click(timeout=7_000)
                    except TypeError:
                        candidate.click()
                    except Exception:
                        try:
                            candidate.evaluate("el => el.click()")
                        except Exception:
                            continue

                    ready = cls._wait_for_ready_gupy_application_page(
                        page,
                        timeout_ms=5_000,
                    )
                    if ready is not None:
                        return ready

                    try:
                        pages = (
                            list(context.pages)
                            if context is not None
                            else [page]
                        )
                    except Exception:
                        pages = [page]

                    for opened in reversed(pages):
                        if cls._gupy_authenticated_candidate_page(opened):
                            try:
                                opened.bring_to_front()
                            except Exception:
                                ...
                            if cls._gupy_application_page_is_ready(opened):
                                return opened

            ready = cls._resolve_ready_gupy_application_page(page)
            if ready is not None:
                return ready

            try:
                page.wait_for_timeout(200)
            except Exception:
                break

        try:
            current_url = str(getattr(page, "url", "") or "")
        except Exception:
            current_url = ""

        raise RuntimeError(
            "Gupy autenticada, mas o formulario de candidatura nao foi aberto. "
            f"Pagina atual: {current_url or 'desconhecida'}."
        )

    @classmethod
    def _gupy_human_verification_visible(cls, page: object) -> bool:
        """Detect a human-verification gate without trying to bypass it."""
        surfaces: list[object] = [page]
        try:
            surfaces.extend(list(page.frames))
        except Exception:
            ...

        phrases = (
            "confirme que é humano",
            "verify you are human",
            "verifying you are human",
        )
        selectors = (
            'iframe[src*="challenges.cloudflare.com"]',
            'input[type="checkbox"]',
        )

        for surface in surfaces:
            for selector in selectors:
                try:
                    locator = surface.locator(selector)
                    if locator.count() and locator.first.is_visible():
                        content = ""
                        try:
                            content = surface.locator("body").inner_text().casefold()
                        except Exception:
                            ...
                        if (
                            "cloudflare" in content
                            or any(phrase in content for phrase in phrases)
                            or "challenges.cloudflare.com" in selector
                        ):
                            return True
                except Exception:
                    continue

            try:
                content = surface.locator("body").inner_text().casefold()
            except Exception:
                continue
            if any(phrase in content for phrase in phrases):
                return True

        return False

    @classmethod
    def _wait_for_gupy_human_verification(
        cls,
        page: object,
        *,
        timeout_ms: int = 300_000,
    ) -> bool:
        """Wait for the user to complete Cloudflare/MFA manually."""
        elapsed = 0
        interval = 1_000

        while elapsed < timeout_ms:
            if cls._gupy_application_page_is_ready(page):
                return True

            # Completing Cloudflare normally leaves the user on the same
            # /candidates/signin page. The disappearance of the verification
            # widget is therefore sufficient to continue with passwordless.
            if not cls._gupy_human_verification_visible(page):
                return True

            try:
                page.wait_for_timeout(interval)
            except Exception:
                return False
            elapsed += interval

        return False

    @staticmethod
    def _gupy_candidate_host(url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return bool(
            parsed.scheme == "https"
            and (host == "gupy.io" or host.endswith(".gupy.io"))
        )

    @classmethod
    def _gupy_authenticated_candidate_page(
        cls,
        page: object,
    ) -> bool:
        """Identify a Gupy candidate page that is no longer an authentication screen."""
        try:
            current_url = str(getattr(page, "url", "") or "")
        except Exception:
            return False

        if not cls._gupy_candidate_host(current_url):
            return False

        normalized = current_url.lower()
        authentication_routes = (
            "/candidates/signin",
            "/candidates/passwordless-signin",
            "/candidates/passwordless-email-sent",
            "/candidates/check-email",
            "/candidates/email-sent",
        )
        if any(route in normalized for route in authentication_routes):
            return False

        if cls._gupy_page_has_visible_password_field(page):
            return False

        return "/candidates/" in normalized

    @classmethod
    def _resolve_authenticated_gupy_page(
        cls,
        page: object,
    ) -> object | None:
        """Return the best controlled page that proves a real Gupy session."""
        try:
            context = page.context
            pages = list(context.pages)
        except Exception:
            pages = [page]

        if page not in pages:
            pages.append(page)

        for candidate in reversed(pages):
            if cls._gupy_application_page_is_ready(candidate):
                try:
                    candidate.bring_to_front()
                except Exception:
                    ...
                return candidate

        for candidate in reversed(pages):
            if cls._gupy_authenticated_candidate_page(candidate):
                try:
                    candidate.bring_to_front()
                except Exception:
                    ...
                return candidate

        return None

    @classmethod
    def _wait_for_gupy_authenticated_page(
        cls,
        page: object,
        *,
        timeout_ms: int = 20_000,
    ) -> object:
        """Wait until passwordless login produces a real authenticated Gupy page.

        Leaving email.gupy.com.br is not sufficient: the magic link can briefly
        land back on /candidates/signin while the session is still being
        established. Authentication is confirmed only by an authenticated
        candidate/application page.
        """
        elapsed = 0
        interval_ms = 200

        while elapsed < timeout_ms:
            authenticated = cls._resolve_authenticated_gupy_page(page)
            if authenticated is not None:
                return authenticated

            try:
                page.wait_for_timeout(interval_ms)
            except Exception:
                time.sleep(interval_ms / 1_000)
            elapsed += interval_ms

        try:
            current_url = str(getattr(page, "url", "") or "")
        except Exception:
            current_url = ""

        raise RuntimeError(
            "O link da Gupy foi aberto, mas a sessão autenticada não foi "
            "confirmada. Página atual: "
            f"{current_url or 'desconhecida'}."
        )

    @staticmethod
    def _gupy_body_text(page: object) -> str:
        """Return normalized visible Gupy text without failing the workflow."""
        try:
            body = page.locator("body")
            return str(body.inner_text() or "").casefold()
        except Exception:
            return ""

    @classmethod
    def _gupy_application_stage(
        cls,
        page: object,
    ) -> GupyApplicationStage:
        """Identify the current authenticated Gupy application stage."""
        try:
            current_url = str(getattr(page, "url", "") or "").casefold()
        except Exception:
            current_url = ""

        body_text = cls._gupy_body_text(page)

        # The final-submission barrier has precedence over generic presentation
        # text so the automation can never advance through it accidentally.
        if any(
            phrase in body_text
            for phrase in (
                "finalizar candidatura",
                "enviar candidatura",
                "concluir candidatura",
            )
        ):
            return GupyApplicationStage.FINAL_SUBMISSION

        if any(
            phrase in body_text
            for phrase in (
                "vamos continuar sua candidatura",
                "continuar sua candidatura?",
            )
        ):
            return GupyApplicationStage.WELCOME

        if any(
            phrase in body_text
            for phrase in (
                "perguntas criadas pela empresa",
                "perguntas da empresa",
                "perguntas eliminatórias",
                "perguntas eliminatorias",
            )
        ):
            return GupyApplicationStage.COMPANY_QUESTIONS

        if any(
            phrase in body_text
            for phrase in (
                "apresente-se!",
                "apresente-se",
                "a empresa deseja saber mais sobre você",
                "a empresa deseja saber mais sobre voce",
            )
        ):
            return GupyApplicationStage.PRESENTATION

        if any(
            phrase in body_text
            for phrase in (
                "dados adicionais",
                "informações adicionais",
                "informacoes adicionais",
            )
        ):
            return GupyApplicationStage.ADDITIONAL_DATA

        if any(
            phrase in body_text
            for phrase in (
                "revisar candidatura",
                "revise sua candidatura",
                "revisão da candidatura",
                "revisao da candidatura",
            )
        ):
            return GupyApplicationStage.REVIEW

        if "/steps/" in current_url:
            return GupyApplicationStage.UNKNOWN

        return GupyApplicationStage.UNKNOWN

    @staticmethod
    def _dismiss_gupy_optional_update_modal(page: object) -> bool:
        """Dismiss only the optional Gupy update modal, never a required dialog."""
        labels = (
            "NÃO, OBRIGADO",
            "Não, obrigado",
            "Nao, obrigado",
        )
        for label in labels:
            try:
                locator = page.get_by_role(
                    "button",
                    name=label,
                    exact=True,
                )
                if locator.count() and locator.first.is_visible():
                    locator.first.click()
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def _click_gupy_authenticated_continue(
        cls,
        page: object,
    ) -> bool:
        """Advance only the authenticated welcome screen."""
        if cls._gupy_application_stage(page) is not GupyApplicationStage.WELCOME:
            return False

        try:
            locator = page.get_by_role(
                "button",
                name="Continuar",
                exact=True,
            )
            if not locator.count() or not locator.first.is_visible():
                return False
            locator.first.scroll_into_view_if_needed(timeout=5_000)
            locator.first.click(timeout=10_000)
            return True
        except TypeError:
            try:
                locator.first.click()
                return True
            except Exception:
                return False
        except Exception:
            return False

    @classmethod
    def _wait_for_gupy_stage_change(
        cls,
        page: object,
        previous: GupyApplicationStage,
        *,
        timeout_ms: int = 8_000,
    ) -> GupyApplicationStage:
        elapsed = 0
        interval_ms = 100

        while elapsed < timeout_ms:
            current = cls._gupy_application_stage(page)
            if current is not previous:
                return current
            try:
                page.wait_for_timeout(interval_ms)
            except Exception:
                break
            elapsed += interval_ms

        return cls._gupy_application_stage(page)

    @staticmethod
    def _gupy_source_label(source_url: str | None) -> str:
        """Map a known vacancy source URL to a Gupy source-channel label."""
        if not source_url:
            return ""

        host = urlparse(source_url).netloc.casefold()
        mappings = (
            ("linkedin.com", "LinkedIn"),
            ("indeed.com", "Indeed"),
            ("infojobs.com", "InfoJobs"),
            ("vagas.com", "Vagas.com"),
        )
        for domain, label in mappings:
            if host == domain or host.endswith(f".{domain}"):
                return label
        return ""

    @classmethod
    def _fill_gupy_source_channel(
        cls,
        page: object,
        source_url: str | None,
    ) -> bool:
        """Fill only the objective 'where did you find this job?' field.

        Referral and current-employment questions are intentionally untouched:
        they require an explicit candidate fact and must not be inferred.
        """
        if cls._gupy_application_stage(page) is not GupyApplicationStage.ADDITIONAL_DATA:
            return False

        source_label = cls._gupy_source_label(source_url)
        if not source_label:
            return False

        field = None
        semantic_candidates: list[object] = []
        for getter in (
            lambda: page.get_by_role(
                "combobox",
                name=re.compile(r"onde você encontrou essa vaga", re.IGNORECASE),
            ),
            lambda: page.get_by_label(
                re.compile(r"onde você encontrou essa vaga", re.IGNORECASE),
            ),
        ):
            try:
                semantic_candidates.append(getter())
            except Exception:
                continue

        for locator in semantic_candidates:
            try:
                if locator.count() and locator.first.is_visible():
                    field = locator.first
                    break
            except Exception:
                continue

        if field is None:
            return False

        try:
            current_value = str(field.input_value() or "").strip().casefold()
            if current_value == source_label.casefold():
                return False
        except Exception:
            ...

        try:
            field.select_option(label=source_label)
            return True
        except Exception:
            ...

        try:
            field.click(timeout=5_000)
        except TypeError:
            try:
                field.click()
            except Exception:
                return False
        except Exception:
            return False

        try:
            option = page.get_by_role(
                "option",
                name=source_label,
                exact=True,
            )
            if option.count() and option.first.is_visible():
                option.first.click(timeout=5_000)
                return True
        except TypeError:
            try:
                option.first.click()
                return True
            except Exception:
                ...
        except Exception:
            ...

        return False

    @classmethod
    def _gupy_additional_data_manual_items(cls, page: object) -> tuple[str, ...]:
        """List additional-data questions that need explicit candidate confirmation."""
        text = cls._gupy_body_text(page)
        pending: list[str] = []

        if any(
            phrase in text
            for phrase in (
                "alguém que trabalha nesta empresa indicou você",
                "alguem que trabalha nesta empresa indicou voce",
            )
        ):
            pending.append("indicação por colaborador")

        if any(
            phrase in text
            for phrase in (
                "você trabalha na empresa",
                "voce trabalha na empresa",
                "você trabalha nesta empresa",
                "voce trabalha nesta empresa",
            )
        ):
            pending.append("vínculo atual com a empresa")

        return tuple(pending)

    @classmethod
    def _prepare_gupy_post_auth(
        cls,
        page: object,
        progress: Callable[[object], None],
        *,
        source_url: str | None = None,
    ) -> object:
        """Handle only safe post-auth transitions before form automation."""
        cls._dismiss_gupy_optional_update_modal(page)
        stage = cls._gupy_application_stage(page)

        if stage is GupyApplicationStage.FINAL_SUBMISSION:
            progress((90, "Gupy pronta para revisão final; envio permanece manual"))
            return page

        if stage is GupyApplicationStage.WELCOME:
            progress((82, "Candidatura autenticada; avançando a tela inicial da Gupy"))
            if not cls._click_gupy_authenticated_continue(page):
                raise RuntimeError(
                    "A tela inicial autenticada da Gupy foi reconhecida, "
                    "mas o botão Continuar não pôde ser acionado."
                )
            stage = cls._wait_for_gupy_stage_change(
                page,
                GupyApplicationStage.WELCOME,
            )
            cls._dismiss_gupy_optional_update_modal(page)

        stage_labels = {
            GupyApplicationStage.ADDITIONAL_DATA: "Dados adicionais",
            GupyApplicationStage.COMPANY_QUESTIONS: "Perguntas da empresa",
            GupyApplicationStage.PRESENTATION: "Apresente-se",
            GupyApplicationStage.REVIEW: "Revisão",
            GupyApplicationStage.FINAL_SUBMISSION: "Finalização manual",
            GupyApplicationStage.UNKNOWN: "Etapa não identificada",
        }
        label = stage_labels.get(stage, stage.value)

        if stage is GupyApplicationStage.FINAL_SUBMISSION:
            progress((90, "Gupy pronta para revisão final; envio permanece manual"))
            return page

        progress((84, f"Etapa pós-autenticação da Gupy: {label}"))

        if stage is GupyApplicationStage.ADDITIONAL_DATA:
            if cls._fill_gupy_source_channel(page, source_url):
                progress((86, "Origem da vaga preenchida automaticamente na Gupy"))

            manual_items = cls._gupy_additional_data_manual_items(page)
            if manual_items:
                progress((87, "Confirmação manual necessária: " + ", ".join(manual_items)))

        return page

    def _prepare_gupy(
        self,
        page: object,
        profile: ApplicantProfile,
        progress: Callable[[object], None],
    ) -> object:
        """Authenticate in Gupy only through the Entrar sem senha button."""
        try:
            application_url = str(getattr(page, "url", "") or "")
        except Exception:
            application_url = ""

        parsed_application = urlparse(application_url)
        host = parsed_application.netloc.lower()

        if (
            parsed_application.scheme != "https"
            or not host
            or not (host == "gupy.io" or host.endswith(".gupy.io"))
        ):
            raise RuntimeError(
                "A URL da candidatura não pertence a um domínio seguro da Gupy."
            )

        self._dismiss_common_banners(page)

        if (
            self._gupy_application_page_is_ready(page)
            or self._gupy_authenticated_candidate_page(page)
        ):
            progress((50, "Sessão da Gupy já autenticada; preenchimento será manual"))
            return page

        # Public job pages such as /jobs/11345819 do not contain candidate
        # authentication controls. Move to the official Gupy sign-in page first.
        current_path = parsed_application.path.lower()
        if current_path.startswith("/jobs/"):
            signin_url = (
                f"{parsed_application.scheme}://{parsed_application.netloc}"
                "/candidates/signin"
            )
            progress((38, "Abrindo a página de acesso da Gupy"))
            page.goto(
                signin_url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

        # From this point the only permitted transition is the explicit
        # passwordless button. Never submit the regular sign-in form.
        page = self._resolve_gupy_candidate_page(page)
        auth_surface = self._gupy_auth_surface(page)
        self._clear_gupy_signin_credentials(auth_surface)

        progress((40, "Clicando no botão Entrar sem senha"))
        self._click_gupy_passwordless_entry(auth_surface, progress)

        page = self._resolve_gupy_candidate_page(page)
        auth_surface = self._gupy_auth_surface(page)

        progress((42, "Validando a página Entrar sem senha da Gupy"))
        self._wait_for_gupy_passwordless_page(auth_surface)

        passwordless_email = profile.email.strip()
        if not passwordless_email or "@" not in passwordless_email:
            raise RuntimeError(
                "O Perfil do Candidato não possui um e-mail válido para "
                "o acesso sem senha da Gupy."
            )

        if not self._fill_gupy_passwordless_email(
            auth_surface,
            passwordless_email,
        ):
            raise RuntimeError(
                "O campo E-mail ou CPF da página Entrar sem senha "
                "não foi localizado."
            )

        if not self._click_gupy_passwordless_continue(auth_surface):
            raise RuntimeError(
                "O botão para continuar o acesso sem senha da Gupy "
                "não foi localizado."
            )

        progress((47, "Selecionando o recebimento do link por e-mail"))
        self._wait_for_gupy_delivery_method_page(auth_surface)

        capture_uid_baseline = getattr(
            self.magic_link_service,
            "capture_sender_uid_baseline",
            None,
        )
        uid_baseline = (
            capture_uid_baseline(progress=progress)
            if callable(capture_uid_baseline)
            else None
        )
        requested_after = datetime.now(UTC)

        if not self._click_first_visible(
            auth_surface,
            (
                "Receber link via e-mail",
                "Receber link por e-mail",
                "Enviar link por e-mail",
            ),
        ):
            raise RuntimeError(
                "O botão Receber link via e-mail da Gupy não foi localizado."
            )

        progress((50, "Confirmando o envio do link de acesso pela Gupy"))
        if not self._wait_for_gupy_link_sent_confirmation(auth_surface):
            raise RuntimeError(
                "A Gupy não confirmou o envio do link de acesso. "
                "A consulta IMAP não foi iniciada."
            )

        progress((62, "Aguardando o e-mail de acesso da Gupy via IMAP"))
        original_timeout = getattr(
            self.magic_link_service,
            "_timeout_seconds",
            None,
        )
        try:
            if original_timeout is not None:
                self.magic_link_service._timeout_seconds = 60
            try:
                magic_link = self.magic_link_service.wait_for_link(
                    email_address=passwordless_email,
                    requested_after=requested_after,
                    min_uid=uid_baseline,
                    progress=progress,
                )
            except TimeoutError:
                progress((
                    64,
                    "E-mail da Gupy não localizado em 1 minuto; solicitando novo link...",
                ))
                resend = auth_surface.get_by_role(
                    "button",
                    name="Reenviar link",
                )
                if not resend.count() or not resend.first.is_visible():
                    resend = auth_surface.get_by_text(
                        "Reenviar link",
                        exact=True,
                    )
                if not resend.count() or not resend.first.is_visible():
                    raise RuntimeError(
                        "O botão Reenviar link da Gupy não foi localizado."
                    ) from None
                if callable(capture_uid_baseline):
                    uid_baseline = capture_uid_baseline(
                        progress=progress,
                    )
                resend.first.click()
                requested_after = datetime.now(UTC)
                progress((
                    65,
                    "Novo link solicitado; aguardando o novo e-mail da Gupy...",
                ))
                magic_link = self.magic_link_service.wait_for_link(
                    email_address=passwordless_email,
                    requested_after=requested_after,
                    min_uid=uid_baseline,
                    progress=progress,
                )
        finally:
            if original_timeout is not None:
                self.magic_link_service._timeout_seconds = original_timeout

        progress((76, "Abrindo o link de acesso recebido via IMAP"))

        target_page = auth_surface
        try:
            target_page.bring_to_front()
        except Exception:
            ...

        target_page.goto(
            magic_link,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        progress((78, "Confirmando a sessão autenticada da Gupy"))
        target_page = self._wait_for_gupy_authenticated_page(
            target_page,
            timeout_ms=20_000,
        )

        progress((
            80,
            "Link da Gupy aberto e autenticação concluída; "
            "preenchimento seguirá manualmente",
        ))
        self._dismiss_common_banners(target_page)
        return target_page

    @staticmethod
    def _resolve_gupy_candidate_page(page: object) -> object:
        """Select the controlled Gupy tab, prioritizing passwordless pages."""
        try:
            context = page.context
            pages = list(context.pages)
        except Exception:
            pages = [page]

        inspected: list[tuple[object, str]] = []
        for candidate in pages:
            try:
                url = str(candidate.url)
            except Exception:
                continue
            inspected.append((candidate, url))

        priorities = (
            "/candidates/passwordless-signin",
            "/candidates/passwordless-email-sent",
            "/candidates/check-email",
            "/candidates/email-sent",
            "/candidates/jobs/",
            "/candidates/signin",
            "/candidates/",
        )
        selected = None
        for route in priorities:
            for candidate, url in reversed(inspected):
                normalized = url.lower()
                if "gupy.io" in normalized and route in normalized:
                    selected = candidate
                    break
            if selected is not None:
                break

        if selected is None:
            controlled_urls = ", ".join(url or "about:blank" for _, url in inspected)
            raise RuntimeError(
                "A página da Gupy não está sob controle do Playwright. "
                f"Abas controladas: {controlled_urls or 'nenhuma'}."
            )

        try:
            selected.bring_to_front()
        except Exception:
            ...
        try:
            selected.wait_for_load_state("domcontentloaded", timeout=20_000)
        except Exception:
            ...
        return selected


    @classmethod
    def _clear_gupy_signin_credentials(cls, page: object) -> None:
        """Neutralize Chrome autofill on the regular Gupy sign-in form."""
        surfaces: list[object] = [page]
        try:
            surfaces.extend(list(page.frames))
        except Exception:
            ...

        for surface in surfaces:
            try:
                surface.evaluate(
                    """
                    () => {
                        for (const input of document.querySelectorAll(
                            'input[type="password"], input[type="email"], '
                            + 'input[autocomplete="username"], '
                            + 'input[name*="email" i], input[id*="email" i], '
                            + 'input[name*="cpf" i], input[id*="cpf" i]'
                        )) {
                            input.setAttribute('autocomplete', 'off');
                            input.value = '';
                            input.dispatchEvent(new Event('input', {bubbles: true}));
                            input.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }
                    """
                )
            except Exception:
                ...

            for selector in (
                'input[type="password"]',
                'input[type="email"]',
                'input[autocomplete="username"]',
                'input[name*="email" i]',
                'input[id*="email" i]',
                'input[name*="cpf" i]',
                'input[id*="cpf" i]',
            ):
                try:
                    locator = surface.locator(selector)
                    for index in range(locator.count()):
                        candidate = locator.nth(index)
                        if candidate.is_visible() and candidate.is_editable():
                            candidate.fill("")
                except Exception:
                    continue


    @classmethod
    def _click_gupy_passwordless_entry(
        cls,
        page: object,
        progress: Callable[[object], None] | None = None,
    ) -> None:
        """Click only Gupy's #passwordlessSignin control."""
        callback = progress or (lambda _value: None)

        try:
            current_url = str(getattr(page, "url", "") or "")
        except Exception:
            current_url = ""

        if "/candidates/passwordless-signin" in current_url.lower():
            return

        cls._clear_gupy_signin_credentials(page)

        # Confirmed in the live Gupy DOM:
        # <button id="passwordlessSignin" aria-label="Entrar sem senha">
        button = page.locator("#passwordlessSignin")

        try:
            button.first.wait_for(state="visible", timeout=15_000)
        except Exception as error:
            raise RuntimeError(
                "O botão Entrar sem senha (#passwordlessSignin) "
                "não foi localizado na página da Gupy."
            ) from error

        callback((40, "Clicando em Entrar sem senha na Gupy"))

        try:
            button.first.scroll_into_view_if_needed(timeout=3_000)
        except Exception:
            ...

        try:
            button.first.click(timeout=10_000)
        except Exception:
            try:
                button.first.evaluate("el => el.click()")
            except Exception as error:
                raise RuntimeError(
                    "Não foi possível acionar o botão Entrar sem senha da Gupy."
                ) from error

        try:
            page.wait_for_url(
                re.compile(r".*/candidates/passwordless-signin(?:[/?#].*)?$"),
                timeout=15_000,
            )
        except Exception:
            try:
                current_url = str(getattr(page, "url", "") or "").lower()
            except Exception:
                current_url = ""

            if "/candidates/passwordless-signin" not in current_url:
                raise RuntimeError(
                    "O botão Entrar sem senha foi acionado, mas a Gupy "
                    "não abriu a rota passwordless."
                ) from None



    @staticmethod
    def _confirm_gupy_passwordless_navigation(page: object) -> None:
        """Require the real passwordless route/form after choosing passwordless."""
        try:
            page.wait_for_url(
                re.compile(r".*/candidates/passwordless-signin(?:[/?#].*)?$"),
                timeout=15_000,
            )
            return
        except Exception:
            ...

        try:
            current_url = str(page.url).lower()
        except Exception:
            current_url = ""

        if "/candidates/passwordless-signin" in current_url:
            return

        # A tenant may render the passwordless form without changing the URL.
        # In that case there must be an editable identifier field and no visible
        # password field.
        try:
            password = page.locator('input[type="password"]')
            if password.count() and password.first.is_visible():
                raise RuntimeError(
                    "A Gupy permaneceu na tela de login com senha."
                )
        except RuntimeError:
            raise
        except Exception:
            ...

        try:
            field = page.get_by_label("E-mail ou CPF", exact=False)
            if (
                field.count()
                and field.first.is_visible()
                and field.first.is_editable()
            ):
                return
        except Exception:
            ...

        raise RuntimeError(
            "A Gupy não abriu a página Entrar sem senha após a seleção."
        )




    @classmethod
    def _wait_for_gupy_passwordless_page(cls, page: object) -> None:
        """Confirm the passwordless route without blocking on input heuristics."""
        try:
            page.wait_for_url(
                re.compile(r".*/candidates/passwordless-signin(?:[/?#].*)?$"),
                timeout=15_000,
            )
        except Exception:
            ...

        try:
            current_url = str(getattr(page, "url", "") or "").lower()
        except Exception:
            current_url = ""

        if "/candidates/passwordless-signin" not in current_url:
            raise RuntimeError(
                "A Gupy não abriu a rota Entrar sem senha."
            )

        if cls._gupy_human_verification_visible(page):
            if not cls._wait_for_gupy_human_verification(page):
                raise RuntimeError(
                    "A confirmação humana da Gupy não foi concluída."
                )

        try:
            password = page.locator('input[type="password"]')
            if password.count() and password.first.is_visible():
                raise RuntimeError(
                    "Proteção Gupy: formulário com senha detectado na rota "
                    "Entrar sem senha."
                )
        except RuntimeError:
            raise
        except Exception:
            ...

    @classmethod
    def _click_gupy_passwordless_continue(cls, page: object) -> bool:
        """Submit the Gupy passwordless identifier form across tenant variants."""
        if cls._click_first_visible(
            page,
            (
                "Continuar",
                "Enviar link",
                "Enviar",
                "Prosseguir",
                "Avançar",
            ),
        ):
            return True

        selectors = (
            'button[type="submit"]',
            'input[type="submit"]',
            'form button:not([type])',
        )
        for selector in selectors:
            try:
                locator = page.locator(selector)
                for index in range(locator.count()):
                    candidate = (
                        locator.nth(index)
                        if hasattr(locator, "nth")
                        else locator.first
                    )
                    if not candidate.is_visible():
                        continue
                    if hasattr(candidate, "is_enabled") and not candidate.is_enabled():
                        continue
                    try:
                        candidate.scroll_into_view_if_needed(timeout=5_000)
                    except Exception:
                        ...
                    try:
                        candidate.click(timeout=10_000)
                    except TypeError:
                        candidate.click()
                    return True
            except Exception:
                continue

        try:
            editable = page.locator(
                'input[type="email"], '
                'input[name*="email" i], '
                'input[id*="email" i], '
                'input[name*="cpf" i], '
                'input[id*="cpf" i]'
            )
            for index in range(editable.count()):
                candidate = (
                    editable.nth(index)
                    if hasattr(editable, "nth")
                    else editable.first
                )
                if candidate.is_visible() and candidate.is_editable():
                    candidate.press("Enter")
                    return True
        except Exception:
            ...

        return False

    @staticmethod
    def _wait_for_gupy_delivery_method_page(page: object) -> None:
        """Wait for Gupy to present e-mail or SMS delivery choices."""
        labels = (
            "Receber link via e-mail",
            "Receber link por e-mail",
            "Enviar link por e-mail",
        )
        for label in labels:
            try:
                page.get_by_role(
                    "button",
                    name=label,
                    exact=False,
                ).first.wait_for(state="visible", timeout=15_000)
                return
            except Exception:
                continue
        raise RuntimeError(
            "A tela de escolha do método de acesso da Gupy não foi carregada."
        )




    @classmethod
    def _fill_gupy_passwordless_email(
        cls,
        page: object,
        email_address: str,
    ) -> bool:
        """Fill the visible identifier field on the Gupy passwordless page."""
        semantic_locators = (
            page.get_by_label("E-mail ou CPF", exact=False),
            page.get_by_label("Email ou CPF", exact=False),
            page.get_by_placeholder("E-mail ou CPF", exact=False),
            page.get_by_placeholder("Email ou CPF", exact=False),
            page.get_by_role("textbox"),
        )

        for locator in semantic_locators:
            try:
                for index in range(locator.count()):
                    candidate = locator.nth(index)
                    if not candidate.is_visible() or not candidate.is_editable():
                        continue
                    candidate.fill("")
                    candidate.fill(email_address)
                    return True
            except Exception:
                continue

        try:
            inputs = page.locator("input")
            for index in range(inputs.count()):
                candidate = inputs.nth(index)
                if not candidate.is_visible() or not candidate.is_editable():
                    continue

                input_type = (
                    candidate.get_attribute("type") or "text"
                ).casefold()
                if input_type in {
                    "password",
                    "hidden",
                    "submit",
                    "button",
                    "checkbox",
                    "radio",
                    "file",
                }:
                    continue

                candidate.fill("")
                candidate.fill(email_address)
                return True
        except Exception:
            ...

        return False

    @classmethod
    def _wait_for_gupy_link_sent_confirmation(
        cls,
        page: object,
    ) -> bool:
        success_patterns = (
            "Link enviado com sucesso",
            "Verifique a caixa de entrada",
            "Reenviar link",
        )
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            for text in success_patterns:
                try:
                    locator = page.get_by_text(text, exact=False)
                    if locator.count() and locator.first.is_visible():
                        return True
                except Exception:
                    continue
            time.sleep(0.5)
        return False

    @staticmethod
    def _click_first_visible(page: object, labels: tuple[str, ...]) -> bool:
        for text in labels:
            for role in ("button", "link"):
                try:
                    locator = page.get_by_role(role, name=text, exact=False)
                    for index in range(locator.count()):
                        candidate = (
                            locator.nth(index)
                            if hasattr(locator, "nth")
                            else locator.first
                        )
                        if not candidate.is_visible():
                            continue
                        try:
                            candidate.scroll_into_view_if_needed(timeout=5_000)
                        except Exception:
                            ...
                        try:
                            candidate.click(timeout=10_000)
                        except TypeError:
                            candidate.click()
                        return True
                except Exception:
                    continue
        return False

    @staticmethod
    def _dismiss_common_banners(page: object) -> None:
        for text in ("Aceitar", "Aceitar todos", "Entendi", "Fechar"):
            try:
                locator = page.get_by_role("button", name=text, exact=False)
                if locator.count() and locator.first.is_visible():
                    locator.first.click()
                    return
            except Exception:
                continue

    @staticmethod
    def _open_default_browser(url: str) -> bool:
        return bool(webbrowser.open(url, new=2))

    @staticmethod
    def _platform(host: str) -> str:
        names = {
            "linkedin": "LinkedIn",
            "gupy": "Gupy",
            "greenhouse": "Greenhouse",
            "lever": "Lever",
            "smartrecruiters": "SmartRecruiters",
            "workday": "Workday",
        }
        return next((label for key, label in names.items() if key in host), host)

    def _fill_profile(self, page: object, profile: ApplicantProfile) -> int:
        values = (
            (("full name", "nome completo", "nome", "name"), profile.full_name),
            (("email", "e-mail"), profile.email),
            (("phone", "telefone", "celular", "whatsapp"), profile.phone),
            (("city", "cidade", "location", "localização"), profile.city),
            (("linkedin", "perfil do linkedin"), profile.linkedin_url),
        )
        filled = 0
        for labels, value in values:
            if value and self._fill_first_matching(page, labels, value):
                filled += 1
        return filled

    @staticmethod
    def _fill_first_matching(page: object, labels: tuple[str, ...], value: str) -> bool:
        for label in labels:
            candidates = (
                page.get_by_label(label, exact=False),
                page.get_by_placeholder(label, exact=False),
                page.locator(
                    f'input[name*="{label}" i], textarea[name*="{label}" i], '
                    f'input[id*="{label}" i], textarea[id*="{label}" i]'
                ),
            )
            for locator in candidates:
                try:
                    if locator.count() and locator.first.is_visible() and locator.first.is_editable():
                        locator.first.fill(value)
                        return True
                except Exception:
                    continue
        return False

    @staticmethod
    def _attach_resume(page: object, resume_path: Path | None) -> bool:
        if resume_path is None or not resume_path.exists():
            return False
        try:
            inputs = page.locator('input[type="file"]')
            for index in range(inputs.count()):
                candidate = inputs.nth(index)
                accept = (candidate.get_attribute("accept") or "").lower()
                if not accept or any(token in accept for token in ("pdf", "doc", "word")):
                    candidate.set_input_files(str(resume_path.resolve()))
                    return True
        except Exception:
            return False
        return False
