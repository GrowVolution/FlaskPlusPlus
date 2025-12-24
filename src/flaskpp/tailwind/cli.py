import typer, subprocess, os

from flaskpp.tailwind import _tailwind_cmd, TailwindError

tailwind = typer.Typer(
    help="Use the tailwind cli using the standalone Flask++ integration."
)


@tailwind.callback(
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def main(
        ctx: typer.Context
):
    args = ctx.args

    result = subprocess.run(
        [_tailwind_cmd(), *args],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise TailwindError(result.stderr)

    typer.echo(result.stdout)


def tailwind_entry(app: typer.Typer):
    app.add_typer(tailwind, name="tailwind")
