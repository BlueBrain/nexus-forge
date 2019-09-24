

# FIXME FIXME FIXME


class IdentifiersHandler:

    def __init__(self, formatter: str) -> None:
        # The formatter is a string containing replacement fields delimited by braces '{}'.
        self.formatter = formatter

    def format(self, *args) -> str:
        return self.formatter.format(args)
