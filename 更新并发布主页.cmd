@echo off
if not defined THESIS_PYTHON set "THESIS_PYTHON=python"
cd /d "%~dp0"
"%THESIS_PYTHON%" scripts\sync_local.py --state "..\thesis_workflow_20261030\project_state.json"
if errorlevel 1 goto finished
"%THESIS_PYTHON%" -m unittest discover -s tests -v
if errorlevel 1 goto finished
"%THESIS_PYTHON%" scripts\build.py
if errorlevel 1 goto finished
"%THESIS_PYTHON%" scripts\publish.py
:finished
pause
