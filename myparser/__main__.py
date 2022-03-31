import typer
import pathlib
import traceback

from myparser.parser import Parser
from myparser.config import get_logger

logger = get_logger(__name__)

parser = Parser()
app = typer.Typer()


@app.command()
def hello(name: str):
    typer.echo(f"Hello {name}")


@app.command()
def parse_file(file: str, out_format: str = 'xlsx'):
    logger.debug('Парсим %s', file)

    cwd = pathlib.Path(__file__).parent.resolve()
    log_file = cwd/'parsing.log'

    try:
        parser.parse_file(file, out_format)

    except Exception as ex:
        logger.error('Ошибка!\n %s', traceback.format_exc())

    logger.debug('Сохранили логи в %s', log_file)


if __name__ == "__main__":
    app()
