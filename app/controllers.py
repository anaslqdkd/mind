class MainController:
    def __init__(self, view):
        self.view = view
        self.view.menubar.quit_action.triggered.connect(self.test)

    def test(self):
        print("T")
