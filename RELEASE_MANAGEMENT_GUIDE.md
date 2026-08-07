"""
ACD Sprint 4.0 - Productization & Distribution Platform

Usage Guide and Integration Examples
"""

# ============================================================================
# OVERVIEW
# ============================================================================

"""
Sprint 4.0 provides complete release management infrastructure:

1. Release Management
   - Semantic versioning (SemVer)
   - Beta and stable release channels
   - Automatic update detection
   - Rollback support

2. Installation System
   - Fresh installation setup
   - Dependency verification
   - Installation integrity checks

3. Update Management
   - Incremental updates
   - Update history tracking
   - Automatic rollback on failure

4. Feature Flags
   - Experimental feature toggling
   - Gradual rollout (percentage-based)
   - Beta feature management

5. Plugin System
   - Dynamic plugin loading
   - Plugin discovery
   - Capability tracking

6. Integrated Documentation
   - Searchable help system
   - Categorized topics
   - Featured articles
"""

# ============================================================================
# BASIC USAGE EXAMPLES
# ============================================================================

def example_initialization():
    """Initialize the release manager."""
    from sqlalchemy.orm import Session
    from acd.application.release import ReleaseManager
    
    session: Session = ...  # Your database session
    database_path = "./acd.db"
    
    # Create release manager
    manager = ReleaseManager(session, database_path)


def example_check_system_status():
    """Check current system status."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Get complete system status
    status = manager.get_system_status()
    
    print(f"Current Version: {status['current_version']}")
    print(f"Status: {status['status']}")
    print(f"Updates Available: {status['updates_available']}")
    print(f"Latest Version: {status['latest_available_version']}")


def example_check_for_updates():
    """Check for available updates."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Check for updates (excluding beta)
    updates = manager.check_for_updates(include_beta=False)
    
    if updates['update_available']:
        print(f"Update available: {updates['latest_version']}")
        print(f"Critical: {updates['is_critical']}")
    else:
        print("System is up to date")


def example_perform_update():
    """Perform a system update."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Perform update from 0.4.0 to 0.5.0
    result = manager.perform_update("0.4.0", "0.5.0")
    
    if result['success']:
        print(f"Update successful!")
        print(f"Backup location: {result['backup_path']}")
    else:
        print(f"Update failed: {result['message']}")


def example_rollback():
    """Rollback to previous version."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Rollback to previous version
    result = manager.rollback_to_previous()
    
    if result['success']:
        print(f"Rolled back to: {result['rolled_back_to']}")
    else:
        print(f"Rollback failed: {result['message']}")


# ============================================================================
# FEATURE FLAGS
# ============================================================================

def example_feature_flags():
    """Use feature flags for experimentation."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Enable a beta feature
    manager.enable_feature("experimental_connector")
    
    # Check if feature is enabled
    if manager.is_feature_enabled("experimental_connector"):
        print("Experimental connector is enabled")
        # Use the feature
    else:
        print("Experimental connector is disabled")
    
    # Disable feature
    manager.disable_feature("experimental_connector")


def example_gradual_rollout():
    """Use feature flags for gradual rollout."""
    from acd.infrastructure.release import FeatureFlagService
    from sqlalchemy.orm import Session
    
    session: Session = ...
    service = FeatureFlagService(session)
    
    # Start with 10% rollout
    service.set_rollout_percentage("new_ai_model", 10)
    
    # Check status for specific user (consistent per user)
    is_enabled = service.is_enabled(
        "new_ai_model",
        current_version="0.4.0",
        user_id="user_123",
    )
    
    # Gradually increase to 50%
    service.set_rollout_percentage("new_ai_model", 50)
    
    # Full rollout
    service.set_rollout_percentage("new_ai_model", 100)


# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

def example_search_help():
    """Search help documentation."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Search for topics
    results = manager.search_help("installation")
    
    for topic in results:
        print(f"- {topic['title']}")
        print(f"  {topic['short_description']}")


def example_get_release_notes():
    """Get release notes."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Get notes for specific version
    notes = manager.get_release_notes("0.5.0")
    print(notes)


# ============================================================================
# PLUGIN SYSTEM
# ============================================================================

def example_load_plugins():
    """Load plugins."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    # Load plugins from directories
    result = manager.load_plugins([
        "./plugins",
        "./optional_connectors",
    ])
    
    print(f"Discovered: {result['discovered']}")
    print(f"Loaded: {result['loaded']}")
    print(f"Plugins: {result['plugins']}")


def example_create_plugin():
    """Create a custom plugin."""
    from acd.infrastructure.release import (
        PluginInterface,
        PluginMetadata,
    )
    
    class CustomConnectorPlugin(PluginInterface):
        """Custom connector plugin."""
        
        def get_metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="custom_connector",
                version="1.0.0",
                author="Your Name",
                description="Custom job connector",
                entry_point="custom_connector:CustomConnectorPlugin",
                min_app_version="0.4.0",
                tags=["connector", "jobs"],
            )
        
        def initialize(self, context: dict) -> bool:
            """Initialize plugin."""
            print(f"Initializing with app version: {context['app_version']}")
            return True
        
        def shutdown(self) -> None:
            """Shutdown plugin."""
            print("Plugin shutting down")
        
        def get_capabilities(self) -> list[str]:
            """Return plugin capabilities."""
            return ["job_scraping", "apply", "tracking"]


# ============================================================================
# DATABASE & VERSIONING
# ============================================================================

def example_migration():
    """Perform database migration."""
    from acd.application.release.services import MigrationService
    from sqlalchemy.orm import Session
    
    session: Session = ...
    service = MigrationService(session)
    
    # Validate compatibility before migration
    compat = service.validate_migration_compatibility("0.3.0", "0.4.0")
    
    if compat["is_compatible"]:
        # Create migration
        result = service.create_migration(
            source_version="0.3.0",
            target_version="0.4.0",
            migration_type="database",
        )
        
        print(f"Migration {result['migration_id']}: {result['message']}")
    else:
        print(f"Migration not compatible: {compat['message']}")


def example_installation():
    """Perform fresh installation."""
    from acd.application.release.services import InstallationService
    from sqlalchemy.orm import Session
    
    session: Session = ...
    service = InstallationService(session, "/opt/acd")
    
    # Check dependencies
    deps = service.check_dependencies()
    if not deps["all_met"]:
        print(f"Missing: {deps['missing_dependencies']}")
        return
    
    # Perform installation
    result = service.perform_fresh_install(
        app_version="0.4.0",
        installation_path="/opt/acd",
        include_default_configs=True,
    )
    
    if result["success"]:
        print(f"Installed at: {result['installation_path']}")
        print(f"Installation ID: {result['installation_id']}")
    else:
        print(f"Installation failed: {result['message']}")


# ============================================================================
# VERSION MANAGEMENT
# ============================================================================

def example_version_operations():
    """Work with semantic versions."""
    from acd.infrastructure.release import (
        SemanticVersion,
        VersionManager,
    )
    
    # Parse and compare versions
    v1 = SemanticVersion("1.0.0")
    v2 = SemanticVersion("1.1.0-beta.1")
    v3 = SemanticVersion("2.0.0")
    
    print(f"{v1} < {v2}: {v1 < v2}")  # True
    print(f"{v2} < {v3}: {v2 < v3}")  # True
    
    # Check release types
    print(f"v1 is major: {v1.is_major_release()}")  # True
    print(f"v2 is beta: {v2.is_beta()}")  # True
    
    # Get next versions
    print(f"Next major: {v1.get_next_major()}")  # 2.0.0
    print(f"Next minor: {v1.get_next_minor()}")  # 1.1.0
    print(f"Next patch: {v1.get_next_patch()}")  # 1.0.1
    
    # Calculate upgrade path
    available = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]
    path = VersionManager.get_upgrade_path("1.0.0", "2.0.0", available)
    print(f"Upgrade path: {path}")


# ============================================================================
# SYSTEM OVERVIEW
# ============================================================================

def example_system_overview():
    """Get complete system overview."""
    from acd.application.release import ReleaseManager
    
    manager: ReleaseManager = ...
    
    overview = manager.get_system_overview()
    
    print("=== ACD System Overview ===")
    print(f"\nStatus: {overview['status']['current_version']}")
    print(f"Installation: {overview['installation_info']['installation_path']}")
    print(f"Dependencies OK: {overview['dependencies']['all_met']}")
    print(f"Verification: {overview['verification']['is_valid']}")
    print(f"\nRecent Updates:")
    for update in overview['update_history'][:3]:
        print(f"  - {update['from_version']} → {update['to_version']}: {update['status']}")
    print(f"\nHelp Topics:")
    for topic in overview['featured_topics'][:3]:
        print(f"  - {topic['title']}")


# ============================================================================
# INTEGRATION WITH EXISTING APPLICATION
# ============================================================================

def example_integration_with_main_app():
    """Integrate release manager into main application."""
    from acd.application.release import ReleaseManager
    from acd.application.platform import PlatformUseCases
    from sqlalchemy.orm import Session
    
    session: Session = ...
    
    # Initialize both systems
    release_manager = ReleaseManager(session)
    platform_use_cases = PlatformUseCases(session)
    
    # Get combined status
    release_status = release_manager.get_system_status()
    health_status = platform_use_cases.get_system_health()
    
    # Check for updates during platform health check
    if health_status['overall_status'] == 'healthy':
        updates = release_manager.check_for_updates()
        if updates['update_available']:
            print(f"Available update: {updates['latest_version']}")


# ============================================================================
# CONFIGURATION
# ============================================================================

"""
Release Management can be configured through:

1. Environment Variables
   - ACD_VERSION: Override current version
   - ACD_INSTALLATION_PATH: Set installation directory
   - ACD_PLUGINS_DIR: Plugin directories
   - ACD_BETA_FEATURES: Enable beta features

2. Database Configuration
   - Use ConfigurationProvider to set values
   - ConfigurationService to manage config

3. Plugin Manifests
   - plugin.json in each plugin directory
   - Defines plugin metadata and requirements

4. Feature Flags
   - Enable/disable features from database
   - Gradual rollout with percentages
   - Version-specific targeting
"""


if __name__ == "__main__":
    print(__doc__)
    print("\nFor detailed examples, see the functions above")
