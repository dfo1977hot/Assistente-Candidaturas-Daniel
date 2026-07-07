from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):

    def __init__(self):

        super().__init__()

        self.addItem("🏠 Dashboard")
        self.addItem("💼 Vagas")
        self.addItem("🏢 Empresas")
        self.addItem("🎯 Candidaturas")
        self.addItem("🗣️ Entrevistas")
        self.addItem("📄 Currículos")
        self.addItem("✉️ Cartas")
        self.addItem("⚙️ Workflows")
        self.addItem("📊 CRM")
        self.addItem("📈 Análise")
        self.addItem("🎯 Planejamento de Carreira")
        self.addItem("🤖 Assistente IA")
        self.addItem("🦾 Agentes")
        self.addItem("⚙ Configurações")

        self.setMaximumWidth(230)
