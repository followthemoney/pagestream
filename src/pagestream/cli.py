#!/usr/bin/python3

import sys
import click
from pathlib import Path
import logging
from . import PDFPageStream

@click.group(help="PDF pagestream utility")
def cli() -> None:
    fmt = "%(name)s [%(levelname)s] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=fmt)

@cli.command("contents", help="Show identified documents in pagestream")
@click.argument('filename', type=click.Path(exists=True))
def contents(filename):
    pagestream = PDFPageStream(filename)
    for pdf in pagestream.get_embedded_documents():
        with pdf.open_metadata() as meta:
            logging.info(meta['dc:title'])
        logging.info("- " + str(len(pdf.pages)) + " pages")

@cli.command("extract", help="Extract documents in pagestream to folder")
@click.argument('filename', type=click.Path(exists=True))
@click.argument('path', type=click.Path())
def extract(filename, path):
    pagestream = PDFPageStream(filename)
    pagestream.extract_to(Path(path))

if __name__ == "__main__":
    cli()
