"""
Handle PDF pagestreams with PikePDF and split them by outline
"""

from re import search
from sys import setrecursionlimit
from logging import info
from pathlib import Path
from pikepdf._qpdf import Pdf, Page

__version__ = "v0.2.2"

# flatten function can recurse a lot, python limits this by default to not
# cause overflows in the CPython implementation
setrecursionlimit(1024 * 1024)

class PDFPageStream:
    """Represents a PDF file that consists of a stream of merged PDF documents"""
    def __init__(self, path: Path):
        self.pdf = Pdf.open(path)

    @staticmethod
    def get_destination(item):
        if item.get('/Dest') is not None:
            return item.get('/Dest')[0]
        elif item.get('/A') is not None and item.get('/A').get('/D') is not None:
            return item.get('/A').get('/D')[0]
        else:
            raise Exception('Outline item has no destination')

    def get_embedded_documents(self):
        with self.pdf.open_outline() as outline:
            for item in outline.root:
                item = item.to_dictionary_object(self.pdf)

                # Could this be an actual embedded document?
                title = item.get('/Title')
                if title is None:
                    continue

                destination = PDFPageStream.get_destination(item)

                # Some outlines are broken and don't have destination target set
                if destination is not None:
                    # First page
                    first = Page(destination).index

                    # last page is either the destination of the next outline item, or the last page of the document
                    next = len(self.pdf.pages)
                    if item.get('/Next') is not None:
                        next_destination = PDFPageStream.get_destination(item.get('/Next'))
                        if next_destination is not None:
                            next = Page(next_destination).index

                    # Is this just a "Page .." reference?
                    regex = "|".join(['Pagina\s?\d+', 'Page\s?\d+', '_Pagina_'])
                    is_literal_page = search(regex, str(title)) is not None
                    is_single_page = next - first == 1

                    if is_literal_page and is_single_page:
                        continue

                    pdf = Pdf.new()
                    with pdf.open_metadata() as meta:
                        meta['dc:title'] = str(title)

                    for page in self.pdf.pages[first:next]:
                        pdf.pages.append(page)

                    yield pdf

    def extract_to(self, output_path):
        """Output split files into path"""
        if not output_path.exists():
            output_path.mkdir(parents=True)

        for pdf in self.get_embedded_documents():
            meta = pdf.open_metadata()
            title = meta['dc:title']

            path = output_path.joinpath(title).with_suffix('.pdf')
            info(f'Extracting {title} to {path}')
            pdf.save(path)


