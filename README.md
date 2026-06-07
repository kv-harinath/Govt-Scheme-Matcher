# Government Scheme Matcher

Lightweight matcher that helps users discover government schemes they are
eligible for based on a simple profile. This workspace contains a FastAPI
backend and a Streamlit frontend.

## Repository layout (important folders)

- `backend/` - FastAPI server, DB access and matching logic
- `frontend/` - Streamlit app (pages, components, utils)
- `ingestion/` - data fetchers and normalisers
- `models/`, `routers/`, `services/` - shared application modules

There is also a duplicated subtree at `govt-scheme-matcher/` which mirrors the
top-level structure — remove or consolidate if this was accidental.

## Quick start (local development)

1. Backend

	 - Create a Python environment and install backend requirements:

	 ```powershell
	 cd backend
	 python -m venv .venv
	 .venv\Scripts\Activate.ps1
	 pip install -r requirements.txt
	 uvicorn main:app --reload --port 8000
	 ```

2. Frontend (Streamlit)

	 - Create a Python environment and install frontend requirements:

	 ```powershell
	 cd frontend
	 python -m venv .venv
	 .venv\Scripts\Activate.ps1
	 pip install -r requirements.txt
	 setx BACKEND_URL "http://localhost:8000"
	 streamlit run app.py
	 ```

	 - The frontend expects the backend URL in the env var `BACKEND_URL`.
	 - JWT authentication is stored in `st.session_state["jwt_token"]` after OTP
		 verification (handled by the login page).

3. Docker (optional)

	 - A `docker-compose.yml` is provided for full-stack runs. Adjust service
		 build contexts before using if the nested `govt-scheme-matcher/` folder
		 duplicates content.

## Git / Remote notes

- Currently this workspace appears to have no commits in the local Git repo.
	Initialize a repo, commit, and add a remote before pushing to GitHub:

```powershell
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-remote-url>
git push -u origin main
```

## Where to look next

- Frontend: [frontend/app.py](frontend/app.py) and pages in [frontend/pages](frontend/pages)
- API helpers: [frontend/utils/api_client.py](frontend/utils/api_client.py)

If you want, I can: (A) create a meaningful initial commit and push the
frontend to your remote, (B) continue generating the remaining frontend files,
or (C) tweak this README further. Which should I do next?

