#!/usr/bin/python3

import sys
import click
import logging
from __init__ import PDFPageStream

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
            print(meta['dc:title'])
        print("- " + str(len(pdf.pages)) + " pages")

if __name__ == "__main__":
    cli()
