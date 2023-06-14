"""
Handle PDF pagestreams with PikePDF and split them by outline
"""

from re import search
from sys import setrecursionlimit
from logging import info
from pathlib import Path
from pikepdf._qpdf import Pdf, Page

__version__ = "v0.2.1"

# flatten function can recurse a lot, python limits this by default to not
# cause overflows in the CPython implementation
setrecursionlimit(1024 * 1024)

class PDFPageStream:
    """Represents a PDF file that consists of a stream of merged PDF documents"""
    def __init__(self, path: Path):
        self.pdf = Pdf.open(path)

    def get_embedded_documents(self):
        with self.pdf.open_outline() as outline:
            for item in outline.root:
                item = item.to_dictionary_object(self.pdf)

                # Could this be an actual embedded document?
                title = item.get('/Title')
                if title is None:
                    continue

                # Some outlines are broken and dont have destination set
                destination = item.get('/A').get('/D')[0]

                if destination is not None:
                    # First page
                    first = Page(destination).index

                    # last page is either the destination of the next outline item, or the last page of the document
                    next = self.pdf.pages[-1].index
                    if item.get('/Next') is not None and item.get('/Next').get('/A').get('/D')[0] is not None:
                        next = Page(item.get('/Next').get('/A').get('/D')[0]).index

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


