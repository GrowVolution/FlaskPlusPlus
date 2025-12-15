@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%SETUP_PY%" (
  echo setup.py not found at: "%SETUP_PY%" 1>&2
  exit /b 1
)

set "PYTHON="
set "PYTHON_ARGS="
call :find_python || (
  echo Python not found. Please install Python 3 and ensure it is on PATH. 1>&2
  exit /b 1
)

if not exist "%VENV_PYTHON%" (
  echo Creating virtual environment in "%VENV_DIR%"...
  "%PYTHON%" %PYTHON_ARGS% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo Failed to create virtual environment. 1>&2
    exit /b 1
  )
)

call :setup_dependencies || (
  echo Failed to setup Flask++, ou may open an issue. ~ https://github.com/GrowVolution/FlaskPlusPlus/issues 1>&2
  exit /b 1
)

rem --------------------------------------
rem -      Flask++ Setup Toolchain       -
rem --------------------------------------

fpp init
fpp modules create example
rem fpp modules install example --src ..\example_module
rem fpp modules install mymodule -s https://github.com/OrgaOrUser/fpp-module
fpp setup
fpp run --interactive


rem --------------------------------------
rem -         Helper Functions           -
rem --------------------------------------

:setup_dependencies
    "%VENV_PYTHON%" -m ensurepip
    if errorlevel 1 exit /b 1
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 exit /b 1
    "%VENV_PYTHON%" -m pip install flaskpp
    if errorlevel 1 exit /b 1
    "%VENV_PYTHON%" -m pip install pywin32
    if errorlevel 1 exit /b 1

:find_python
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=py"
      set "PYTHON_ARGS=-3"
      goto :eof
    )
    py -c "import sys" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=py"
      set "PYTHON_ARGS="
      goto :eof
    )
  )

  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=python"
      goto :eof
    )
  )

  where python3 >nul 2>&1
  if not errorlevel 1 (
    python3 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=python3"
      goto :eof
    )
  )
  exit /b 1
