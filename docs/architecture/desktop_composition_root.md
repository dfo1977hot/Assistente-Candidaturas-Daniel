# Desktop Composition Root

Previously, `app.py` created `MainWindow` directly, so the desktop startup had
no authorized place to connect concrete repositories, Query Adapters,
Application services, and Presentation dependencies.

`DesktopCompositionRoot` is the sole desktop assembly point. It initializes the
database lifecycle and explicitly constructs repositories, Query Adapters,
Application Contexts, use cases, ViewModels, pages, router, and `MainWindow`.
It does not instantiate `Kernel`, `Bootstrap`, `DependencyContainer`, or call
`register_application_composition`. `MainWindow` receives completed objects and
does not resolve dependencies. Repositories keep their existing per-operation
session lifecycle; the root does not retain database sessions.

`app.py` only creates `QApplication`, applies the theme, obtains `MainWindow`
from the root, and starts the event loop. `MainWindow`, Pages, widgets, and
ViewModels do not resolve the container or import Infrastructure.
