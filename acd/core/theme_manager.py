from pathlib import Path


class ThemeManager:

    @staticmethod
    def load(app):

        theme = Path("acd/resources/styles/dark.qss")

        if theme.exists():

            app.setStyleSheet(
                theme.read_text(
                    encoding="utf-8"
                )
            )