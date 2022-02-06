class Generator:
    doc = __revit__.ActiveUIDocument.Document

    def __init__(self, transaction, as_designed_family):
        self.transaction = transaction

