@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "SETUP_PY=%SCRIPT_DIR%\setup.py"
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

if exist "%SCRIPT_DIR%\.requirements.txt" (
  echo Installing dependencies from .requirements.txt...
  "%VENV_PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  "%VENV_PYTHON%" -m pip install -r "%SCRIPT_DIR%\.requirements.txt"
  if errorlevel 1 exit /b 1
  "%VENV_PYTHON%" -m pip install pywin32
  if errorlevel 1 exit /b 1
) else if exist "%SCRIPT_DIR%\requirements.txt" (
  echo Installing dependencies from requirements.txt...
  "%VENV_PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  "%VENV_PYTHON%" -m pip install -r "%SCRIPT_DIR%\requirements.txt"
  if errorlevel 1 exit /b 1
  "%VENV_PYTHON%" -m pip install pywin32
  if errorlevel 1 exit /b 1
)

call :ensure_babel || (
  echo Failed to ensure Babel/pybabel availability. 1>&2
  exit /b 1
)

call :generate_fs_translations || (
  echo Failed to generate/compile translation catalogs. 1>&2
  exit /b 1
)

echo Running setup.py with "%VENV_PYTHON%"...
"%VENV_PYTHON%" "%SETUP_PY%"
exit /b %errorlevel%


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


:ensure_babel
  "%VENV_PYTHON%" -m pip show Babel >nul 2>&1
  if errorlevel 1 (
    echo Installing Babel in venv...
    "%VENV_PYTHON%" -m pip install Babel
    if errorlevel 1 exit /b 1
  )

  set "PYBABEL=%VENV_DIR%\Scripts\pybabel.exe"
  if not exist "%PYBABEL%" set "PYBABEL=%VENV_DIR%\Scripts\pybabel"
  if exist "%PYBABEL%" (
    set "PYBABEL_USE_MODULE="
    exit /b 0
  )

  set "PYBABEL_USE_MODULE=1"
  exit /b 0


:generate_fs_translations
  set "CFG=%SCRIPT_DIR%\babel.cfg"
  set "POT=%SCRIPT_DIR%\messages.pot"
  set "TRANS=%SCRIPT_DIR%\translations"

  if not exist "%TRANS%" mkdir "%TRANS%"

  if not exist "%CFG%" (
    set "CFG=%SCRIPT_DIR%\.babel.fallback.cfg"
    >"%CFG%" echo [python: **/**.py]
    >>"%CFG%" echo.
    >>"%CFG%" echo [jinja2: **/templates/**.html]
    >>"%CFG%" echo extensions=jinja2.ext.i18n
  )

  echo Extracting messages to "%POT%"...
  if defined PYBABEL_USE_MODULE (
    call "%VENV_PYTHON%" -m babel.messages.frontend extract -F "%CFG%" -o "%POT%" "%SCRIPT_DIR%"
  ) else (
    call "%PYBABEL%" extract -F "%CFG%" -o "%POT%" "%SCRIPT_DIR%"
  )
  if errorlevel 1 exit /b 1

  if exist "%TRANS%\en\LC_MESSAGES\messages.po" (
    echo "Updating existing catalogs (en)..."
    if defined PYBABEL_USE_MODULE (
      "%VENV_PYTHON%" -m babel.messages.frontend update -i "%POT%" -d "%TRANS%"
    ) else (
      "%PYBABEL%" update -i "%POT%" -d "%TRANS%"
    )
  ) else (
    echo "Initializing catalogs (en)..."
    if defined PYBABEL_USE_MODULE (
      "%VENV_PYTHON%" -m babel.messages.frontend init -i "%POT%" -d "%TRANS%" -l en
    ) else (
      "%PYBABEL%" init -i "%POT%" -d "%TRANS%" -l en
    )
  )
  if errorlevel 1 exit /b 1

  echo Compiling catalogs...
  if defined PYBABEL_USE_MODULE (
    "%VENV_PYTHON%" -m babel.messages.frontend compile -d "%TRANS%"
  ) else (
    "%PYBABEL%" compile -d "%TRANS%"
  )
  if errorlevel 1 exit /b 1

  exit /b 0
