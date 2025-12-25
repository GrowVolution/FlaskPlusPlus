import typer, subprocess, os

from flaskpp.fpp_node import _node_cmd, _node_env, NodeError


def node(ctx: typer.Context):
    if not ctx.args:
        typer.echo(typer.style("Usage: fpp node <command> [args]", bold=True, fg=typer.colors.YELLOW))
        raise typer.Exit(1)

    command = ctx.args[0]
    args = ctx.args[1:]

    result = subprocess.run(
        [_node_cmd(command), *args],
        cwd=os.getcwd(),
        env=_node_env(),
    )

    if result.returncode != 0:
        raise NodeError("Node command failed.")


def node_entry(app: typer.Typer):
    app.command(
        context_settings={
            "allow_extra_args": True,
            "ignore_unknown_options": True,
        }
    )(node)
