from unittest.mock import patch
from pathlib import Path

from flaskpp.cli import app
from . import runner


@patch("flaskpp.modules.cli.module_home", new_callable=lambda: Path("modules"))
@patch("flaskpp.modules.cli.Repo.clone_from")
def test_modules_install(mock_clone, mock_home):
    with runner.isolated_filesystem():
        local_mod = Path("example_module")
        local_mod.mkdir(parents=True)

        result = runner.invoke(
            app,
            ["modules", "install", "example", "--src", "example_module"]
        )
        assert result.exit_code == 0
        assert "Loading module from local path..." in result.stdout
        assert mock_clone.call_count == 0

        result = runner.invoke(
            app,
            ["modules", "install", "i18n", "--src", "https://github.com/GrowVolution/FPP_i18n_module"]
        )
        assert result.exit_code == 0
        assert "Loading module from remote repository..." in result.stdout

        mock_clone.assert_called_once()


@patch("flaskpp.modules.cli.module_home", new_callable=lambda: Path("modules"))
@patch("flaskpp.modules.cli.prompt_yes_no")
def test_modules_create(mock_prompt, mock_home):
    mock_prompt.return_value = False

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["modules", "create", "test"])

        assert result.exit_code == 0
        assert "successfully created" in result.stdout.lower()
        assert mock_prompt.called
        assert Path("modules/test").exists()
