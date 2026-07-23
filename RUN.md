# Run and test guide

## 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## 3. Configure environment variables

Create a local `.env` file based on `.env.example` and set at least:

```env
GROQ_API_KEY=your_key_here
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
SUPABASE_DB_URL=postgresql://user:password@host:5432/postgres
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 4. Run the API locally

```powershell
uvicorn mains:dapp --reload --host 0.0.0.0 --port 8000
```

Open:
- http://localhost:8000/docs for Swagger UI
- http://localhost:8000/health for the health check

## 5. Test the main endpoints

### Health check
```powershell
curl http://localhost:8000/health
```

### Ask endpoint
```powershell
curl -X POST http://localhost:8000/ai/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -d '{"question":"What projects have I built?"}'
```

### Resume generation
```powershell
curl -X POST http://localhost:8000/resume/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -d '{"job_description":"Python backend engineer"}'
```

## 6. Run syntax checks

```powershell
python -m compileall .
```

## 7. Optional: run unit tests

If you add pytest later:

```powershell
pip install pytest
pytest -q
```
