FastAPI backend scaffold for MY_AI_Interview

Quick start

1. Create virtualenv and install:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set `MONGODB_URL` and `JWT_SECRET`.

3. Run dev server:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
