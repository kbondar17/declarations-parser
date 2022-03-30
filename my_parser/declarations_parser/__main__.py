import typer

from my_parser.declarations_parser.parser import Parser
parser = Parser()
app = typer.Typer()


@app.command()
def hello(name: str):
    typer.echo(f"Hello {name}")


@app.command()
def parse_file(file: str, out_format: str='xlsx'):
    parser.parse_file(file, out_format)
    # if formal:
    #     typer.echo(f"Goodbye Ms. {name}. Have a good day.")
    # else:
    #     typer.echo(f"Bye {name}!")


if __name__ == "__main__":
    app()
