from kgforge.core import Resource, Resources


class Files:

    def __init__(self):
        print("FIXME - Files")

    def download(self, dirpath: str) -> None:
        print("FIXME - Files.download()")


class Dataset(Resource):
    RESERVED = {"files", "parts", "with_parts", "with_files"}

    def __init__(self, **properties) -> None:
        if not self.RESERVED.isdisjoint(set(properties.keys())):
            # FIXME Should be generalized in commons/exceptions.
            raise NotImplementedError(f"Given properties contain a reserved name")
        super().__init__(**properties)

    def parts(self) -> Resources:
        print("FIXME - Dataset.parts()")
        return Resources([])

    def files(self) -> Files:
        print("FIXME - Dataset.with_parts()")
        return Files()

    def with_parts(data: Resources, versioned=True) -> None:
        print("FIXME - Dataset.with_parts()")

    def with_files(self, dirpath) -> None
        print("FIXME - Dataset.with_files()")
