from flask import Blueprint


class App(Blueprint):
    def __init__(self, import_name: str):
        super().__init__("app", import_name)
        self.name = ""
