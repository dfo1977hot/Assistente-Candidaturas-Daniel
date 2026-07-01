from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):

    def __init__(self):

        super().__init__()

        self.addItem("🏠 Dashboard")
        self.addItem("💼 Vagas")
        self.addItem("🏢 Empresas")
        self.addItem("🎯 Candidaturas")
        self.addItem("� Entrevistas")
        self.addItem("�📄 Currículos")
        self.addItem("✉️ Cartas")
        self.addItem("🎯 Entrevistas")
        self.addItem("📊 CRM")
        self.addItem("⚙ Configurações")

        self.setMaximumWidth(230)