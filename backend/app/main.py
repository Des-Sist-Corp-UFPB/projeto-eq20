"""Ponto de entrada principal da aplicação FastAPI modularizada."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.seed import init_db_with_retry
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.ocorrencias import router as ocorrencias_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa banco de dados com retry na inicialização
    init_db_with_retry()
    yield


app = FastAPI(
    title="UrbanaCare API Pro",
    description="API de Gerenciamento de Ocorrências com Autenticação e Admin Dashboard",
    lifespan=lifespan,
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos roteadores da API
app.include_router(auth_router)
app.include_router(ocorrencias_router)
app.include_router(admin_router)

# Configuração para servir o frontend estático compilado (SPA) se existir
import os
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.exists(static_dir):
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        if not catchall:
            catchall = "index.html"
            
        # Proteção contra path traversal
        resolved_path = os.path.abspath(os.path.join(static_dir, catchall))
        if not resolved_path.startswith(os.path.abspath(static_dir)):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
            
        if os.path.isfile(resolved_path):
            return FileResponse(resolved_path)
            
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

