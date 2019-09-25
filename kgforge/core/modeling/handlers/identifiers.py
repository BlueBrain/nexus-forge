class IdentifiersHandler:

    def __init__(self, formatter: str) -> None:
        # The formatter is a string with replacement fields delimited by braces '{}'.
        self._formatter = formatter

    def format(self, *args) -> str:
        return self._formatter.format(*args)
