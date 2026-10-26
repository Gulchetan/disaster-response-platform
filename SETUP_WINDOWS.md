# Windows setup (SSL / pip / venv)

## What went wrong

1. **`pip install` failed** with `CERTIFICATE_VERIFY_FAILED` — common on corporate networks that inspect HTTPS. Nothing was installed into `.venv`.
2. **`alembic` not found** — Alembic is installed *inside* the venv; use `python -m alembic`, not a global `alembic` command.
3. **`uvicorn` used Python 3.14 globally** — you ran `uvicorn` without the venv module path, so it missed project dependencies (`jose`, `geoalchemy2`, etc.).

## Fix (recommended)

From `disaster-platform`:

```powershell
.\scripts\setup.ps1
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed_data
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Always prefix with **`.\.venv\Scripts\python.exe -m`** so the same interpreter gets all packages.

## Manual pip (if setup.ps1 is blocked)

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

## Proper SSL fix (better than trusted-host)

If your company uses a custom root CA, point pip/Python at it:

```powershell
$env:PIP_CERT="C:\path\to\company-root-ca.pem"
$env:SSL_CERT_FILE="C:\path\to\company-root-ca.pem"
pip install -r requirements.txt
```

Ask IT for the **root CA certificate** used for HTTPS inspection.

## Verify

```powershell
.\.venv\Scripts\python.exe -c "import fastapi, jose, geoalchemy2, alembic; print('OK')"
```

Should print `OK` with no errors.

## Neon: `channel_binding` error

If seed/API fails with `connect() got an unexpected keyword argument 'channel_binding'`, your Neon URL includes libpq-only params. The app strips those for **asyncpg** automatically (see `app/config.py`). Pull latest code or update that file, then retry seed.
