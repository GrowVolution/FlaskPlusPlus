import typer

tests = typer.Typer(help="Test your Flask++ apps and modules.")

# TODO: Implement test cli features later.

def tests_entry(app: typer.Typer):
    app.add_typer(tests, name="test")
