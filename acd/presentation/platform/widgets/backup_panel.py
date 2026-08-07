"""Backup management panel widget."""

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


class BackupPanel(QWidget):
    """Widget for backup management."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize backup panel.

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

        create_btn = QPushButton("Create Backup")
        create_btn.clicked.connect(self.create_backup)
        button_layout.addWidget(create_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Backups table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Type", "Status", "Size (MB)", "Created", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refresh backups list."""
        try:
            backups = self.use_cases.list_backups()
            self.update_table(backups)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load backups: {str(e)}")

    def create_backup(self) -> None:
        """Create new backup."""
        try:
            result = self.use_cases.create_backup()
            QMessageBox.information(
                self,
                "Success",
                f"Backup created: {result['name']}\nSize: {result['size_mb']:.2f}MB",
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup: {str(e)}")

    def update_table(self, backups: list) -> None:
        """Update backups table.

        Args:
            backups: List of backups
        """
        self.table.setRowCount(len(backups))

        for row, backup in enumerate(backups):
            self.table.setItem(row, 0, QTableWidgetItem(backup.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(backup.get("type", "")))
            self.table.setItem(row, 2, QTableWidgetItem(backup.get("status", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{backup.get('size_mb', 0):.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(backup.get("created_at", "")))

            restore_btn = QPushButton("Restore")
            restore_btn.clicked.connect(lambda checked, bid=backup["id"]: self.restore_backup(bid))
            self.table.setCellWidget(row, 5, restore_btn)

    def restore_backup(self, backup_id: int) -> None:
        """Restore from backup.

        Args:
            backup_id: Backup ID
        """
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore backup {backup_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.use_cases.restore_from_backup(
                    backup_id
                )
                QMessageBox.information(self, "Success", "Backup restored successfully")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore backup: {str(e)}")
