@echo off
if "%STUDY_PYTHON%"=="" set "STUDY_PYTHON=python"
"%STUDY_PYTHON%" scripts/55_complete_study.py %*
exit /b %errorlevel%
