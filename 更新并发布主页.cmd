@echo off
set "TASK_PY=C:\Users\Lenovo\miniconda3\envs\ultralytics\python.exe"
cd /d "%~dp0"
"%TASK_PY%" scripts\sync_local.py --state "..\thesis_workflow_20261030\project_state.json"
if errorlevel 1 goto finished
"%TASK_PY%" -m unittest discover -s tests -v
if errorlevel 1 goto finished
"%TASK_PY%" scripts\build.py
if errorlevel 1 goto finished
"%TASK_PY%" scripts\publish.py
:finished
pause
