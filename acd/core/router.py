class Router:

    def __init__(self):

        self.stack = None

        self.pages = {}

    def set_stack(self, stack):

        self.stack = stack

    def register(self, name, widget):

        self.pages[name] = widget

        self.stack.addWidget(widget)

    def navigate(self, name):

        widget = self.pages.get(name)

        if widget:

            self.stack.setCurrentWidget(widget)