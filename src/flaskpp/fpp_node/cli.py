import typer, subprocess, os

from flaskpp.fpp_node import _node_cmd, NodeError

node = typer.Typer(
    help="Run node commands using the portable Flask++ node bundle. (Behaves like normal node.)"
)


@node.callback(
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def main(
    ctx: typer.Context,
    command: str = typer.Argument(
        "npm",
        help="The node command to execute",
    )
):
    args = ctx.args

    result = subprocess.run(
        [_node_cmd(command), *args],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise NodeError(result.stderr)

    typer.echo(result.stdout)


def node_entry(app: typer.Typer):
    app.add_typer(node, name="node")
