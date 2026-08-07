"""Settings editor panel widget."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from acd.application.platform import PlatformUseCases


class SettingsPanel(QWidget):
    """Widget for settings management."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize settings panel.

        Args:
            use_cases: Platform use cases
            parent: Parent widget
        """
        super().__init__(parent)
        self.use_cases = use_cases
        self.setup_ui()
        self.refresh()

    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout()

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_config)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Settings table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Key", "Value", "Type", "Category"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table)

        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        layout.addWidget(save_btn)

        self.setLayout(layout)
        self.current_changes = {}

    def refresh(self) -> None:
        """Refresh settings."""
        try:
            configs = self.use_cases.export_configuration()
            self.update_table(configs)
            self.current_changes = {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {str(e)}")

    def update_table(self, configs: dict) -> None:
        """Update settings table.

        Args:
            configs: Configuration dictionary
        """
        self.table.setRowCount(len(configs))

        for row, (key, config) in enumerate(configs.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))

            value_item = QTableWidgetItem(str(config.get("value", "")))
            value_item.setData(256, key)  # Store key for identification
            self.table.setItem(row, 1, value_item)

            self.table.setItem(row, 2, QTableWidgetItem(config.get("type", "")))
            self.table.setItem(row, 3, QTableWidgetItem(config.get("category", "")))

    def on_item_changed(self, item) -> None:
        """Track item changes.

        Args:
            item: Changed item
        """
        if item.column() == 1:  # Value column
            key = item.data(256)
            if key:
                self.current_changes[key] = item.text()

    def save_changes(self) -> None:
        """Save configuration changes."""
        if not self.current_changes:
            QMessageBox.information(self, "Info", "No changes to save")
            return

        try:
            for key, value in self.current_changes.items():
                self.use_cases.set_config(key, value)

            QMessageBox.information(self, "Success", f"Saved {len(self.current_changes)} changes")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def export_config(self) -> None:
        """Export configuration."""
        try:
            configs = self.use_cases.export_configuration()
            QMessageBox.information(self, "Success", f"Exported {len(configs)} configuration items")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
