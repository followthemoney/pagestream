#!/usr/bin/python3

import sys
import click
import logging

@click.group(help="PDF pagestream utility")
def cli() -> None:
    fmt = "%(name)s [%(levelname)s] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=fmt)

@cli.command("contents", help="Show identified documents in pagestream")
@click.argument("archive")
def contents(archive):
    click.echo(f"Extract {archive}")


