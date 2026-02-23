import secrets
from dotenv import load_dotenv
import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session, Mapped, mapped_column
from redis import Redis
import json
from celery_app import calcular_fatorial, calcular_soma

# CONFIGURAÇÕES
load_dotenv()

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente {name} não definida")
    return value

app = FastAPI(title="API de Livros")
DATABASE_URL = require_env("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
security = HTTPBasic()
meu_usuario = require_env("API_USER")
minha_senha = require_env("API_PASSWORD")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass

def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, meu_usuario)
    is_password_correct = secrets.compare_digest(credentials.password, minha_senha)

    if not(is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos!",
            headers={"WWW-Authenticate": "Basic"}
        )
    
#Models
class LivroDB(Base):
    __tablename__="livros"

    id: Mapped[int] = mapped_column(index=True, primary_key=True, autoincrement=True)
    nome_livro: Mapped[str] = mapped_column(nullable=False)
    autor_livro: Mapped[str] = mapped_column(nullable=False)
    ano_livro: Mapped[int] = mapped_column(nullable=False)

#Executa a criação do banco de dados e das tabelas.
Base.metadata.create_all(bind=engine)

#Schemas
class livro_schema(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int
    
#Funções auxiliares
async def salvar_livros_redis(cache_key, response):
    redis_client.setex(cache_key, 60, json.dumps(response))
    
async def deletar_livros_redis():
    cached_keys = redis_client.scan_iter("livros:*")
    if not cached_keys:
        return
    for key in cached_keys:
        redis_client.delete(key)

#Endpoints da minha API
@app.get("/healthy")
def healthy_check():
    return {"message": "Healthy"}

@app.get("/debug/redis")
def get_livros_redis(credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    cached_keys = list(redis_client.scan_iter("livros:*"))
    if not cached_keys:
        return {"message": "nenhum item cadastrado no redis"}
    
    return [{
        "key": key,
        "ttl": redis_client.ttl(key),
        "valor": json.loads(redis_client.get(key))
    } for key in cached_keys]

@app.get("/livros")
async def get_livros(session: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario), page:int = 1, limit:int = 10):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page ou Limit não podem ser menor do que 1")
    cache_key = f"livros:page={page}:limit={limit}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    livros = session.query(LivroDB).offset((page - 1) * limit).limit(limit).all()
    response = {
        "page": page,
        "limit": limit,
        "total": session.query(func.count(LivroDB.id)).scalar(),
        "livros": [{
            "id": livro.id,
            "nome_livro": livro.nome_livro,
            "autor_livro": livro.autor_livro,
            "ano_livro": livro.ano_livro
        } for livro in livros]
    }
    await salvar_livros_redis(cache_key, response)
    return response

@app.post("/livros")
async def post_livro(livro: livro_schema, session: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    novo_livro = LivroDB(nome_livro=livro.nome_livro, autor_livro=livro.autor_livro, ano_livro=livro.ano_livro)
    session.add(novo_livro)
    session.commit()
    await deletar_livros_redis()
    return {"message": "Livro cadastrado com sucesso"}

@app.put("/livros/{id}")
async def update_livro(livro: livro_schema, id:int, session: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    query_livro = session.query(LivroDB).filter(LivroDB.id == id).first()
    if not query_livro:
        raise HTTPException(status_code=400, detail="Não existe livro cadastrado com esse ID")
    query_livro.nome_livro = livro.nome_livro
    query_livro.autor_livro = livro.autor_livro
    query_livro.ano_livro = livro.ano_livro
    session.commit()
    await deletar_livros_redis()
    return {"message": "Livro atualizado com sucesso"}

@app.delete("/livros/{id}")
async def delete_livro(id:int, session: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    query_livro = session.query(LivroDB).filter(LivroDB.id == id).first()
    if not query_livro:
        raise HTTPException(status_code=400, detail="Nâo existe livro cadastrado com esse id")
    session.delete(query_livro)
    session.commit()
    await deletar_livros_redis()
    return {"message": "Livro deletado com sucesso"}

@app.post("/calcular/soma")
async def calcula_soma(a:int, b:int):
    task = calcular_soma.delay(a, b)
    return {
        "task_id": task.id,
        "status": task.status,
        "message": "Tarefa de calcular soma disparada com sucesso"
    }

@app.post("/calcular/fatorial")
async def calcula_fatorial(n: int):
    task = calcular_fatorial.delay(n)
    return {
        "task_id": task.id,
        "status": task.status,
        "message": "Tarefa de calcular fatorial disparada com sucesso"
    }

@app.get("/fila_celery")
async def listar_fila():
    fila = redis_client.lrange("celery", 0, -1)
    tasks = [json.loads(task) for task in fila]
    return {
        "total": len(tasks),
        "tasks": tasks
    }