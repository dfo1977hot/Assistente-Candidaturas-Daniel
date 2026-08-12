"""Playwright adapter for assisted, never unattended, job applications."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
import re
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen
import webbrowser

from acd.infrastructure.email.gupy_magic_link_service import GupyMagicLinkService
from acd.services.assisted_application_service import (
    ApplicantProfile,
    AssistedApplicationResult,
)
from acd.services.linkedin_application_resolver import LinkedInApplicationResolution


class PlaywrightApplicationBrowser:
    """Open and prefill supported forms, leaving final submission to the user."""

    def __init__(
        self,
        magic_link_service: GupyMagicLinkService | None = None,
        *,
        linkedin_headless: bool | Callable[[], bool] = False,
    ) -> None:
        self.magic_link_service = magic_link_service or GupyMagicLinkService()
        self._linkedin_headless = linkedin_headless

    def _linkedin_runs_headless(self) -> bool:
        value = self._linkedin_headless
        return bool(value() if callable(value) else value)

    def has_email_credential(self, email_address: str) -> bool:
        return self.magic_link_service.has_credential(email_address)

    def save_email_credential(self, email_address: str, password: str) -> None:
        self.magic_link_service.save_credential(email_address, password)

    _PROFILE_DIR = Path("data/browser_profiles/assisted_applications")

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

        if platform == "Gupy":
            parsed = urlparse(url)
            login_url = f"{parsed.scheme}://{parsed.netloc}/candidates/signin"
            progress((30, "Abrindo a página de login da Gupy"))
            if not self._open_default_browser(login_url):
                raise RuntimeError(
                    "Não foi possível abrir a página de login da Gupy."
                )
            progress((100, "Login da Gupy aberto para candidatura manual"))
            return AssistedApplicationResult(
                platform=platform,
                url=login_url,
                fields_filled=0,
                resume_attached=False,
                linkedin_restricted_mode=False,
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
                headless=False,
                viewport={"width": 1366, "height": 900},
                args=["--start-maximized"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            progress((35, f"Abrindo candidatura na {platform}"))

            if platform == "Gupy":
                self._prepare_gupy(page, profile, progress)

            progress((55, "Identificando e preenchendo campos visíveis"))
            fields_filled = self._fill_profile(page, profile)
            resume_attached = self._attach_resume(page, resume_path)
            progress((80, "Currículo anexado" if resume_attached else "Currículo aguardando anexo"))
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

    def _prepare_gupy(
        self,
        page: object,
        profile: ApplicantProfile,
        progress: Callable[[object], None],
    ) -> None:
        """Authenticate through Gupy passwordless login and stop before submission."""
        self._dismiss_common_banners(page)
        self._click_first_visible(
            page,
            (
                "Candidatar-se",
                "Quero me candidatar",
                "Iniciar candidatura",
                "Continuar candidatura",
                "Aplicar para esta vaga",
            ),
        )
        page.wait_for_timeout(1_000)

        # A Gupy pode abrir o login em outra aba. Passe a operar
        # explicitamente na página cuja URL é da Gupy e contém /candidates/.
        page = self._resolve_gupy_candidate_page(page)

        progress((40, "Acionando Entrar sem senha na Gupy"))
        self._click_gupy_passwordless_entry(page)

        progress((42, "Abrindo a página de acesso sem senha da Gupy"))
        self._wait_for_gupy_passwordless_page(page)

        email_filled = self._fill_gupy_passwordless_email(page, profile.email)
        if not email_filled:
            raise RuntimeError(
                "O campo E-mail ou CPF da página Entrar sem senha não foi localizado."
            )

        if not self._click_first_visible(page, ("Continuar", "Enviar link")):
            raise RuntimeError(
                "O botão Continuar da página Entrar sem senha não foi localizado."
            )

        progress((47, "Selecionando o recebimento do link por e-mail"))
        self._wait_for_gupy_delivery_method_page(page)
        requested_after = datetime.now(UTC)
        if not self._click_first_visible(
            page,
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
        if not self._wait_for_gupy_link_sent_confirmation(page):
            raise RuntimeError(
                "A Gupy não confirmou o envio do link de acesso. "
                "A consulta ao e-mail não foi iniciada."
            )

        magic_link = self.magic_link_service.wait_for_link(
            email_address=profile.email,
            requested_after=requested_after,
            progress=progress,
        )
        progress((76, "Abrindo o acesso seguro da Gupy"))
        page.goto(magic_link, wait_until="domcontentloaded", timeout=60_000)
        self._dismiss_common_banners(page)

    @staticmethod
    def _resolve_gupy_candidate_page(page: object) -> object:
        """Select the exact Gupy sign-in page from every controlled tab."""
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
            "/candidates/signin",
            "/candidates/passwordless-signin",
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
                "A página de login da Gupy não está sob controle do Playwright. "
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
    def _click_gupy_passwordless_entry(cls, page: object) -> None:
        """Click the confirmed Gupy button and report the real controlled page."""
        try:
            current_url = str(page.url)
        except Exception:
            current_url = ""
        if "/candidates/passwordless-signin" in current_url.lower():
            return

        try:
            page.wait_for_load_state("domcontentloaded", timeout=20_000)
        except Exception:
            ...
        selectors = (
            "#passwordlessSignin",
            'button[aria-label="Entrar sem senha"]',
        )
        last_error: Exception | None = None
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() < 1:
                    continue
                button = locator.first
                button.wait_for(state="visible", timeout=20_000)
                if hasattr(button, "is_enabled") and not button.is_enabled():
                    raise RuntimeError(
                        "O botão Entrar sem senha está visível, mas desabilitado."
                    )
                try:
                    button.scroll_into_view_if_needed(timeout=5_000)
                except Exception:
                    ...
                try:
                    button.click(timeout=15_000)
                except TypeError:
                    button.click()
                except Exception:
                    if hasattr(button, "evaluate"):
                        button.evaluate("element => element.click()")
                    else:
                        button.click()
                cls._confirm_gupy_passwordless_navigation(page)
                return
            except Exception as error:
                last_error = error

        try:
            count = page.locator("#passwordlessSignin").count()
        except Exception:
            count = -1
        raise RuntimeError(
            "Não foi possível acionar Entrar sem senha na aba controlada da Gupy. "
            f"URL controlada: {current_url or 'desconhecida'}; "
            f"#passwordlessSignin encontrados: {count}."
        ) from last_error

    @staticmethod
    def _confirm_gupy_passwordless_navigation(page: object) -> None:
        """Require the passwordless route or form after clicking its entry control."""
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

        try:
            field = page.get_by_label("E-mail ou CPF", exact=False)
            if field.count():
                field.first.wait_for(state="visible", timeout=8_000)
                return
        except Exception:
            ...
        try:
            page.get_by_text("Entrar sem senha", exact=False).first.wait_for(
                state="visible",
                timeout=5_000,
            )
            return
        except Exception as error:
            raise RuntimeError(
                "A Gupy não abriu a página Entrar sem senha após o clique."
            ) from error

    @staticmethod
    def _wait_for_gupy_passwordless_page(page: object) -> None:
        """Wait until the dedicated passwordless form is actually available."""
        try:
            page.wait_for_url(
                re.compile(r".*/candidates/passwordless-signin(?:[/?#].*)?$"),
                timeout=15_000,
            )
        except Exception:
            # Some Gupy tenants update the form without a full navigation.
            ...
        try:
            page.get_by_text("Entrar sem senha", exact=False).first.wait_for(
                state="visible",
                timeout=10_000,
            )
        except Exception as error:
            raise RuntimeError(
                "A página Entrar sem senha da Gupy não foi carregada."
            ) from error

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
        """Fill the new, blank field shown after choosing passwordless access."""
        selectors = (
            page.get_by_label("E-mail ou CPF", exact=False),
            page.get_by_placeholder("E-mail ou CPF", exact=False),
            page.locator('input[type="email"]'),
            page.locator(
                'input[name*="email" i], input[id*="email" i], '
                'input[name*="cpf" i], input[id*="cpf" i]'
            ),
        )
        for locator in selectors:
            try:
                if (
                    locator.count()
                    and locator.first.is_visible()
                    and locator.first.is_editable()
                ):
                    locator.first.fill("")
                    locator.first.fill(email_address)
                    return True
            except Exception:
                continue
        return cls._fill_first_matching(
            page,
            ("e-mail ou cpf", "email ou cpf", "e-mail", "email"),
            email_address,
        )

    @staticmethod
    def _wait_for_gupy_link_sent_confirmation(page: object) -> bool:
        """Confirm that Gupy accepted the request before polling the mailbox."""
        confirmation = re.compile(
            r"(enviamos|enviado|verifique|confira).{0,80}"
            r"(e-?mail|caixa de entrada|link)",
            re.IGNORECASE,
        )
        try:
            page.get_by_text(confirmation).first.wait_for(
                state="visible",
                timeout=15_000,
            )
            return True
        except Exception:
            ...
        # A successful request can also navigate to a confirmation route.
        try:
            current_url = str(page.url).lower()
        except Exception:
            current_url = ""
        return any(
            token in current_url
            for token in ("passwordless-email-sent", "check-email", "email-sent")
        )

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
