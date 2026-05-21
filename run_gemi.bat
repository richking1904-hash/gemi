@echo off
cd /d "%~dp0"
:: uv 대신 직접 파이썬 실행으로 변경 (가장 확실함)
.\venv\Scripts\python.exe main.py
pause