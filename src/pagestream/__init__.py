"""
Handle PDF pagestreams with PikePDF and split them by outline
"""

from re import search
from sys import setrecursionlimit
from logging import info
from typing import List
from pathlib import Path
from pikepdf._qpdf import Pdf, Page
from pikepdf.models.outlines import OutlineItem
from itertools import tee, chain

__version__ = "0.1.2"

# flatten function can recurse a lot, python limits this by default to not
# cause overflows in the CPython implementation
setrecursionlimit(1024 * 1024)

def flatten(items: List[OutlineItem]):
    """Recursively flatten a outline tree"""
    if len(items) == 0:
        return items
    if len(items[0].children) > 0:
        return flatten(items[0].children) + flatten(items[1:])
    return items[:1] + flatten(items[1:])

def is_valid_outlineitem(item: OutlineItem):
    """Check wether outline item has a page destination"""
    if item.action is None:
        return False
    else:
        # https://opensource.adobe.com/dc-acrobat-sdk-docs/library/pdfmark/pdfmark_Actions.html
        # TODO - There's more valid actions than only `FitH`
        return item.action.get('/D').as_list()[1] == '/FitH'

class PDFPageStream:
    """Represents a PDF file that consists of a stream of merged PDF documents"""
    def __init__(self, path: Path):
        self.pdf = Pdf.open(path)

    def get_outline_items(self):
        """Get valid outlineitems (items with destination)"""
        with self.pdf.open_outline() as outline:
            return list(filter(is_valid_outlineitem, flatten(outline.root)))

    def can_extract_by_outline(self):
        """Could this PDF document stream be seperated by PDF outline"""
        # Some outlines are to short
        items = self.get_outline_items()
        if len(items) <= 1:
            return False

        # Some outlines just have references to each page in the stream
        # TODO - This regex tests for dutch and english outline items that all
        # spell "Page", this could be improved by checking if every outline
        # item only references subsequent pages
        regex = "|".join(['Pagina\s?\d+', 'Page\s?\d+', '_Pagina_'])
        if all(map(lambda i: search(regex, i.title) is not None, items)):
            return False

        # Some outlines have references to the same page in the document
        pages = map(lambda i: Page(i.action.get('/D')[0]).index, items)
        a, b = tee(pages)
        if len(set(a)) != len(list(b)):
            return False

        return True

    def extract_to(self, output_path):
        """Split PDF file into seperate files"""
        if not output_path.exists():
            output_path.mkdir(parents=True)

        items = self.get_outline_items()
        page_indexes = map(lambda i: Page(i.action.get('/D')[0]).index, items)
        titles = map(lambda i: i.title, items)

        # Get 2 iterators over the page numbers & advance the second iterator by one
        from_pages, to_pages = tee(page_indexes)
        next(to_pages)
        # Add last page of PDF as end of last document & merge back into 1 iterator
        documents = zip(titles, from_pages, chain(to_pages, [len(self.pdf.pages)]))

        for title, from_page, to_page in documents:
            # Create new PDF & append from src
            pdf = Pdf.new()
            for page in self.pdf.pages[from_page:to_page]:
                pdf.pages.append(page)

            path = output_path.joinpath(title).with_suffix('.pdf')
            info(f'Extracting {title} to {path}')
            pdf.save(path)
