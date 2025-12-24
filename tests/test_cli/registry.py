from unittest.mock import patch
from pathlib import Path

from flaskpp.cli import app
from flaskpp.utils.service_registry import service_file
from . import runner


@patch("flaskpp.utils.service_registry._ensure_admin", return_value=True)
@patch("flaskpp.utils.service_registry.subprocess.run")
def test_registry_register(mock_run, mock_admin):
    with runner.isolated_filesystem():
        with patch("flaskpp.utils.service_registry.home", Path.cwd()):
            with patch("flaskpp.utils.service_registry.service_path", Path("services")):
                Path("services").mkdir()

                result = runner.invoke(
                    app,
                    ["registry", "register", "testapp", "--port", "5000", "--debug"]
                )
                assert result.exit_code == 0
                assert "Service testapp registered." in result.stdout
                assert mock_run.call_count >= 3
                sf = service_file("testapp")
                assert sf.exists()


@patch("flaskpp.utils.service_registry.subprocess.run")
def test_registry_start(mock_run):
    with runner.isolated_filesystem():
        with patch("flaskpp.utils.service_registry.home", Path.cwd()):
            with patch("flaskpp.utils.service_registry.service_path", Path("services")):
                Path("services").mkdir()
                result = runner.invoke(
                    app,
                    ["registry", "start", "testapp"]
                )
                assert result.exit_code == 0
                assert "Service testapp started." in result.stdout
                mock_run.assert_called_once()


@patch("flaskpp.utils.service_registry.subprocess.run")
def test_registry_stop(mock_run):
    with runner.isolated_filesystem():
        with patch("flaskpp.utils.service_registry.home", Path.cwd()):
            with patch("flaskpp.utils.service_registry.service_path", Path("services")):
                Path("services").mkdir()
                result = runner.invoke(
                    app,
                    ["registry", "stop", "testapp"]
                )
                assert result.exit_code == 0
                assert "Service testapp stopped." in result.stdout
                mock_run.assert_called_once()


@patch("flaskpp.utils.service_registry._ensure_admin", return_value=True)
@patch("flaskpp.utils.service_registry.subprocess.run")
def test_registry_remove(mock_run, mock_admin):
    with runner.isolated_filesystem():
        with patch("flaskpp.utils.service_registry.home", Path.cwd()):
            with patch("flaskpp.utils.service_registry.service_path", Path("services")):
                Path("services").mkdir()
                sf = service_file("testapp")
                sf.write_text("x")

                result = runner.invoke(
                    app,
                    ["registry", "remove", "testapp"]
                )
                assert result.exit_code == 0
                assert "Service testapp removed." in result.stdout
                assert mock_run.call_count >= 2
                assert not sf.exists()
