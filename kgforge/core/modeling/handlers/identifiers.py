class IdentifiersHandler:

    def __init__(self, formatter: str) -> None:
        self.formatter = formatter

    def format(self, *args) -> str:
        return self.formatter.format(args)
