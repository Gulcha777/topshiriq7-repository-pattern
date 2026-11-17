@echo off
cd /d "%~dp0"
pip install -q -r requirements.txt
if not exist .env copy .env.example .env

for %%m in (demo_repository demo_transaction demo_cache demo_sqli) do (
  echo === python -m app.%%m ===
  python -m app.%%m || exit /b 1
  echo.
)
echo === pytest ===
python -m pytest -q
