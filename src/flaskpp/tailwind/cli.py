import typer, subprocess, os

from flaskpp.tailwind import _tailwind_cmd, TailwindError


def tailwind(ctx: typer.Context):
    if not ctx.args:
        typer.echo(typer.style("Usage: fpp tailwind -- [args]", bold=True))
        raise typer.Exit(1)

    args = ctx.args[0:]

    result = subprocess.run(
        [_tailwind_cmd(), *args],
        cwd=os.getcwd()
    )

    if result.returncode != 0:
        raise TailwindError("Tailwind command failed.")

    typer.echo(result.stdout)


def tailwind_entry(app: typer.Typer):
    app.command(
        context_settings={
            "allow_extra_args": True,
            "ignore_unknown_options": True,
        }
    )(tailwind)
