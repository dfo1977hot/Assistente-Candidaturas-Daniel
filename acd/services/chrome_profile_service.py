"""Google Chrome persistent-profile support for assisted applications."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


@dataclass(frozen=True, slots=True)
class ChromeProfileStatus:
    """Human-readable state of the dedicated ACD Chrome profile."""

    profile_dir: Path
    chrome_executable: Path | None
    initialized: bool

    @property
    def available(self) -> bool:
        return self.chrome_executable is not None


class ChromeProfileService:
    """Manage the dedicated Chrome profile without storing Google passwords."""

    PROFILE_DIR = Path("data/browser_profiles/acd_chrome")

    _WINDOWS_CANDIDATES = (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    )

    def profile_dir(self) -> Path:
        return self.PROFILE_DIR.resolve()

    def chrome_executable(self) -> Path | None:
        discovered = shutil.which("chrome") or shutil.which("chrome.exe")
        if discovered:
            path = Path(discovered)
            if path.is_file():
                return path

        for candidate in self._WINDOWS_CANDIDATES:
            if candidate.is_file():
                return candidate
        return None

    def status(self) -> ChromeProfileStatus:
        profile_dir = self.profile_dir()
        return ChromeProfileStatus(
            profile_dir=profile_dir,
            chrome_executable=self.chrome_executable(),
            initialized=profile_dir.exists() and any(profile_dir.iterdir()),
        )

    def open_for_google_authentication(self) -> ChromeProfileStatus:
        executable = self.chrome_executable()
        if executable is None:
            raise RuntimeError(
                "Google Chrome não foi encontrado neste computador."
            )

        profile_dir = self.profile_dir()
        profile_dir.mkdir(parents=True, exist_ok=True)

        subprocess.Popen(
            [
                str(executable),
                f"--user-data-dir={profile_dir}",
                "--start-maximized",
                "https://accounts.google.com/",
            ],
            close_fds=True,
        )
        return self.status()
