from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Column
from rich.traceback import install
import logging
from rich.logging import RichHandler

log = logging.getLogger("rich")
console = Console()
progress = Progress(
    TextColumn(
        "[progress.description]{task.description}",
        table_column=Column(width=50),
    ),
    BarColumn(bar_width=None),
    MofNCompleteColumn(table_column=Column(width=10, justify="right")),
    console=console,
    expand=True,
    transient=True,
)


def setup_logging():
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )
    install()
