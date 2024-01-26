import os
import sys
import logging

import typer

from repoform.app import RepoForm
from repoform.loaders import DataLoaderType


logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

help_text = dict(
    modules_path = "Path to the modules to load.",
    data_path = "Path to the data to load.",
    data_loader_type = ".",
    debug = "Enable debug logging."
)

app = typer.Typer(add_completion=False)
repoform = RepoForm()


def setup(modules_path: str, debug: bool):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    full_path = os.path.join(os.getcwd(), modules_path)

    sys.path.append(full_path)


@app.command()
def init(
    modules_path: str = typer.Argument(..., help=help_text["modules_path"]),
    data_path: str = typer.Argument(..., help=help_text["data_path"]),
    debug: bool = typer.Option(False, help=help_text["debug"])
):
    """
    Show registered methods and registered data.
    """
    setup(modules_path, debug)

    repoform.load(modules_path, data_path, DataLoaderType.YAMLFilesToDictLoader)
    repoform.log_registered_items()


@app.command()
def plan(
    modules_path: str = typer.Argument(..., help=help_text["modules_path"]),
    debug: bool = typer.Option(False, help=help_text["debug"])
):
    """
    Plan changes (dry-run).
    """
    setup(modules_path, debug)

    repoform.load(modules_path)
    repoform.plan_changes()
    typer.echo(f"Planning done!")


@app.command()
def apply(
    modules_path: str = typer.Argument(..., help=help_text["modules_path"]),
    debug: bool = typer.Option(False, help=help_text["debug"])
):
    """
    Apply changes.
    """
    setup(modules_path, debug)

    repoform.load(modules_path)
    repoform.apply_changes()
    typer.echo(f"Changes done!")


if __name__ == "__main__":
    app()
