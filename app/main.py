# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings
warnings.filterwarnings("ignore")
from app.api import router as api_router
#from app.state import SESSIONS, TEXTS, INDEX  # <— now comes from state

app = FastAPI(title="JD Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api_router)
