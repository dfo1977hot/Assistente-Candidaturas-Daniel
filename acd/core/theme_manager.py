from importlib.resources import files


class ThemeManager:

    @staticmethod
    def load(app):

        theme = files("acd").joinpath("resources", "styles", "dark.qss")

        if theme.exists():

            app.setStyleSheet(theme.read_text(encoding="utf-8"))
