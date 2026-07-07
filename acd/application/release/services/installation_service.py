"""Installation service for initial setup."""

import platform
import sys
from datetime import datetime
from pathlib import Path

from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.release import VersionManager
from acd.infrastructure.repositories.release import ReleaseRepository


class InstallationService:
    """Handle installation and initial configuration."""

    def __init__(self, session, installation_path: str = "./"):
        """Initialize installation service.

        Args:
            session: SQLAlchemy database session
            installation_path: Path where application is installed
        """
        self.session = session
        self.installation_path = Path(installation_path)
        self.repository = ReleaseRepository(session)
        self.logger = StructuredLogger("InstallationService")

    def perform_fresh_install(
        self,
        app_version: str,
        installation_path: str,
        include_default_configs: bool = True,
    ) -> dict:
        """Perform fresh installation.

        Returns:
            Installation result {success, message, installation_id, duration_seconds}
        """
        start_time = datetime.now()
        log_entry = None

        try:
            # Create installation log
            log_entry = self.repository.create_installation_log(
                operation="INSTALL",
                status="IN_PROGRESS",
                message=f"Starting fresh installation of v{app_version}",
                details={
                    "installation_path": installation_path,
                    "os": platform.system(),
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                },
            )

            with self.logger.operation("fresh_install"):
                # Verify version format
                try:
                    VersionManager.parse_version(app_version)
                except ValueError:
                    raise ValueError(f"Invalid version format: {app_version}")

                # Create installation directory
                install_dir = Path(installation_path)
                install_dir.mkdir(parents=True, exist_ok=True)

                # Create default config directories
                if include_default_configs:
                    config_dir = install_dir / "config"
                    backup_dir = install_dir / "backups"
                    log_dir = install_dir / "logs"
                    data_dir = install_dir / "data"

                    for dir_path in [config_dir, backup_dir, log_dir, data_dir]:
                        dir_path.mkdir(parents=True, exist_ok=True)

                # Create or update installed version record
                from acd.domain.release import InstallationStatus

                installed = self.repository.get_or_create_installed_version(app_version)
                installed.installation_path = str(install_dir.absolute())
                installed.installation_type = InstallationStatus.FRESH_INSTALL.value
                installed.status = InstallationStatus.ACTIVE.value
                installed.installation_date = datetime.now()
                installed.system_info = {
                    "os": platform.system(),
                    "os_version": platform.release(),
                    "python_version": sys.version,
                    "architecture": platform.machine(),
                }
                self.session.commit()

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()

                # Update log
                self.repository.update_installation_log(
                    log_entry.id,
                    status="SUCCESS",
                    duration_seconds=int(duration),
                )

                self.logger.info(
                    "fresh_install_completed",
                    f"Installation completed successfully in {duration:.1f} seconds",
                )

                return {
                    "success": True,
                    "message": f"ACD v{app_version} installed successfully",
                    "installation_path": str(install_dir.absolute()),
                    "installation_id": installed.id,
                    "duration_seconds": int(duration),
                }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            # Update log with error
            if log_entry:
                self.repository.update_installation_log(
                    log_entry.id,
                    status="FAILED",
                    duration_seconds=int(duration),
                    error_message=str(e),
                )

            self.logger.error(
                "fresh_install_failed",
                f"Installation failed: {str(e)}",
                error_type=type(e).__name__,
            )

            return {
                "success": False,
                "message": f"Installation failed: {str(e)}",
                "installation_id": None,
                "duration_seconds": int(duration),
            }

    def check_dependencies(self) -> dict:
        """Check if all dependencies are met.

        Returns:
            {
                "all_met": bool,
                "missing_dependencies": list,
                "system_info": dict,
            }
        """
        import importlib

        missing = []
        required_packages = [
            "sqlalchemy",
            "pyside6",
            "psutil",
            "requests",
        ]

        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing.append(package)

        return {
            "all_met": len(missing) == 0,
            "missing_dependencies": missing,
            "system_info": {
                "os": platform.system(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "python_executable": sys.executable,
            },
        }

    def verify_installation(self) -> dict:
        """Verify installation integrity.

        Returns:
            {
                "is_valid": bool,
                "errors": list,
                "warnings": list,
            }
        """
        errors = []
        warnings = []

        # Check installation directory
        if not self.installation_path.exists():
            errors.append(f"Installation directory not found: {self.installation_path}")

        # Check required subdirectories
        required_dirs = ["config", "backups", "logs", "data"]
        for dir_name in required_dirs:
            dir_path = self.installation_path / dir_name
            if not dir_path.exists():
                warnings.append(f"Directory not found: {dir_path}")

        # Check installed version record
        installed = self.repository.get_installed_version()
        if not installed:
            errors.append("No installed version record found")

        # Check dependencies
        deps_check = self.check_dependencies()
        if not deps_check["all_met"]:
            errors.extend([f"Missing: {pkg}" for pkg in deps_check["missing_dependencies"]])

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def get_installation_info(self) -> dict:
        """Get current installation information."""
        installed = self.repository.get_installed_version()

        if not installed:
            return {
                "installed": False,
                "version": None,
                "installation_path": None,
            }

        return {
            "installed": True,
            "version": installed.current_version,
            "installation_path": installed.installation_path,
            "installation_date": installed.installation_date.isoformat(),
            "status": installed.status,
            "is_beta": installed.is_beta,
        }
