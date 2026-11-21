
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"

app = FastAPI(title="LLM Analyzer")

class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

class AnalysisResponse(BaseModel):
    resume: str
    sentiment: str         
    mots_cles: list[str]

SYSTEM_PROMPT = (
    "Tu es un assistant d'analyse de texte. "
    "Tu réponds uniquement en JSON, en français, avec les champs : "
    "resume (une phrase), sentiment (positif, négatif ou neutre), "
    "mots_cles (liste de 3 à 5 mots)."
)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(req: TextRequest):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.text},
        ],
        "format": AnalysisResponse.model_json_schema(),  # sortie JSON contrainte
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(OLLAMA_URL, json=payload)
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur Ollama : {e}")

    content = r.json()["message"]["content"]
    try:
        return AnalysisResponse.model_validate_json(content)
    except Exception:
        raise HTTPException(status_code=502, detail="Réponse du modèle invalide")