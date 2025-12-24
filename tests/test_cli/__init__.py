from typer.testing import CliRunner
from importlib.metadata import version
from unittest.mock import patch
from pathlib import Path

from flaskpp.cli import app
from flaskpp.tests import test_config

runner = CliRunner()


def test_fpp_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("flaskpp") in result.stdout


def test_fpp_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


@patch("flaskpp.cli.setup_tailwind")
@patch("flaskpp.cli.load_node")
@patch("flaskpp.cli.prepare_vite")
@patch("flaskpp.cli.subprocess.run")
def test_fpp_init(mock_run, mock_prepare, mock_load, mock_tailwind):
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert mock_run.call_count == 3
        assert "Flask++ project successfully initialized." in result.stdout

        mock_prepare.assert_called_once()
        mock_load.assert_called_once()
        mock_tailwind.assert_called_once()


@patch("flaskpp.utils.setup.prompt_yes_no")
@patch("flaskpp.utils.setup.input")
def test_fpp_setup(mock_input, mock_prompt):
    mock_input.return_value = ""
    mock_prompt.return_value = False

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["setup"])

        assert result.exit_code == 0
        assert "Setup complete." in result.stdout
        assert mock_input.call_count > 1
        assert mock_prompt.call_count > 1


@patch("flaskpp.utils.run.subprocess.Popen")
def test_fpp_run(mock_popen):
    with runner.isolated_filesystem():
        Path("app_configs").mkdir()

        Path("app_configs/test.conf").write_text(test_config)

        result = runner.invoke(
            app,
            ["run", "-a", "test", "-p", "80", "-d"]
        )

        mock_popen.assert_called_once()
        assert result.exit_code == 0
        assert "running on http://0.0.0.0:80" in result.stdout
