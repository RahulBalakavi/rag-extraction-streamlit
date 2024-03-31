
class PDFExtractedDataPage:
    def __init__(self):
        self.text = []
        self.sections = []
        self.images = []
        self.tables = []


class PDFExtractedData:

    def __init__(self):
        self.pages = []

    def __str__(self):
        return self.pages

    def __repr__(self):
        return self.pages

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, item):
        return self.pages[item]

    def __len__(self):
        return len(self.pages)

    def __contains__(self, page):
        return page in self.pages

    def __add__(self, other):
        self.pages.append(other.pages)

    def __iadd__(self, other):
        self.pages += other.pages