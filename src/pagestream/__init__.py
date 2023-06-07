"""
Handle PDF pagestreams with PikePDF and split them by outline
"""

from re import search
from sys import setrecursionlimit
from logging import info
from pathlib import Path
from pikepdf._qpdf import Pdf, Page

__version__ = "v0.2.0"

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
                # TODO - Intent here is to not extract single pages that are
                # just named something like "page <x>", there's better ways to do this
                regex = "|".join(['Pagina\s?\d+', 'Page\s?\d+', '_Pagina_'])
                is_literal_page = search(regex, str(title)) is not None
                is_single_page = item.get('/Count') is None
                if is_literal_page and is_single_page:
                    continue

                # Create new PDF & append from src
                pdf = Pdf.new()
                with pdf.open_metadata() as meta:
                    meta['dc:title'] = str(title)

                if not is_single_page:
                    next = item.get('/First')
                    while next is not None:
                        pdf.pages.append(Page(next.get('/Dest')[0]))
                        next = next.get('/Next')
                else:
                    pdf.pages.append(Page(item.get('/A').get('/D')[0]))

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


