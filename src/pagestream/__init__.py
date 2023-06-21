"""
Handle PDF pagestreams with PikePDF and split them by outline
"""

from re import search
from sys import setrecursionlimit
from logging import info, debug
from pathlib import Path
from pikepdf._qpdf import Pdf, Page

__version__ = "v0.2.4"

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
            destination = item.get('/Dest')
        elif item.get('/A') is not None and item.get('/A').get('/D') is not None:
            destination = item.get('/A').get('/D')
        else:
            raise Exception('Outline item has no destination')

        if destination[0] is None:
            raise Exception('Outline item destination has invalid target')

        return destination[0]

    def get_embedded_documents(self):
        with self.pdf.open_outline() as outline:
            for item in outline.root:
                item = item.to_dictionary_object(self.pdf)

                # Could this be an actual embedded document?
                title = item.get('/Title')
                if title is None:
                    continue

                try:
                    destination = PDFPageStream.get_destination(item)
                except Exception as e:
                    debug(e)
                    continue

                # First page
                first = Page(destination).index

                # last page is either the destination of the next outline item, or the last page of the document
                next = None
                while next is None:
                    if item.get('/Next') is not None:
                        # Only use target of next outline item if it's valid
                        try:
                            next_destination = PDFPageStream.get_destination(item.get('/Next'))
                            next = Page(next_destination).index
                        except Exception as e:
                            # If the target is invalid, try the target of the next outline item
                            debug(e)
                            item = item.get('/Next')

                            continue
                    else:
                        next = len(self.pdf.pages)

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

    def extract_to(self, path: Path):
        """Output split files into path"""
        path.mkdir(parents=True, exist_ok=True)

        for pdf in self.get_embedded_documents():
            meta = pdf.open_metadata()
            title = meta['dc:title']

            info(f'Extracting {title}')
            pdf.save(path.joinpath(title).with_suffix('.pdf'))


