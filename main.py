from fastapi import FastAPI, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import csv
import io

# --- 1. CONFIGURAÇÃO INICIAL E DB ---
load_dotenv()

# Lendo variáveis do ambiente (.env)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "fastapi_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "users")

app = FastAPI(title="MongoDB User API")
client: Optional[AsyncIOMotorClient] = None
users_collection = None

# --- 2. MODELOS PYDANTIC ---

# 1. Modelo de Entrada (POST /users/)
class UserCreate(BaseModel):
    nome: str = Field(min_length=3, description="Nome do usuário")
    idade: int = Field(gt=0, description="A idade deve ser maior que zero")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Carla Mendes",
                "idade": 28,
            }
        }
    }

# 2. Modelo de Saída (GET /users/, Resposta do POST)
class UserDB(BaseModel):
    # Usamos Any para aceitar o ObjectId na entrada
    id: Optional[Any] = Field(alias="_id", default=None) 
    nome: str
    idade: int

    model_config = {
        "populate_by_name": True, # Permite que o alias _id seja usado na criação
        "arbitrary_types_allowed": True, # Permite que o campo 'id' aceite ObjectId
        "json_encoders": {ObjectId: str}, # CORREÇÃO: Força ObjectId a ser serializado como string JSON
        "json_schema_extra": {
            "example": {
                "id": "60d0fe4f6e6e7c7a5f3d3b7e",
                "nome": "Carla Mendes",
                "idade": 28,
            }
        }
    }

# --- 3. EVENTOS DE LIFESPAN (CONEXÃO) ---

@app.on_event("startup")
async def startup_db_client():
    """Conecta ao MongoDB ao iniciar o FastAPI."""
    global client, users_collection
    
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="MONGO_URI não configurado no .env")

    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        users_collection = db[COLLECTION_NAME]
        
        # Teste de conexão
        await client.admin.command('ping') 
        print("✅ Conectado com sucesso ao MongoDB!")

    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB. Detalhe: {e}")
        # Levanta a exceção para que o Uvicorn falhe e não inicie a API com DB quebrado
        raise RuntimeError(f"Falha na inicialização da conexão com o DB: {e}")

        
@app.on_event("shutdown")
async def shutdown_db_client():
    """Fecha a conexão com o MongoDB ao desligar o FastAPI."""
    global client
    if client:
        client.close()
        print("🔌 Conexão com MongoDB fechada.")

# --- 4. ENDPOINTS DA API ---

## 1. Criar Usuário (POST)
@app.post("/users/", response_model=UserDB, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    # ... código de verificação ...
    
    user_data = user.model_dump() 
    
    insert_result = await users_collection.insert_one(user_data)
    
    # Busca o documento recém-criado
    created_user = await users_collection.find_one({"_id": insert_result.inserted_id})
    
    # 🚨 CORREÇÃO: Força a conversão do _id para 'id' (string) ANTES de retornar
    created_user['id'] = str(created_user.pop('_id'))
    
    return created_user # Retorna o dicionário com 'id' (str)
## 2. Listar Usuários (GET)
@app.get("/users/", response_model=List[UserDB]) 
async def list_users():
    """
    Retorna todos os usuários da collection do MongoDB, convertendo ObjectId explicitamente.
    """
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Serviço de Banco de Dados Indisponível")

    users = [] 
    
    async for document in users_collection.find():
        
        # 🚨 CORREÇÃO: Converte o _id para string e renomeia o campo no documento
        document['id'] = str(document.pop('_id'))
        
        # Agora o documento tem 'id' (str), 'nome' e 'idade'.
        # O Pydantic model_validate aceita isso sem problemas.
        users.append(UserDB.model_validate(document)) 
        
    return users

## 3. Upload de Usuários (Endpoint POST para Inserção em Massa)
@app.post("/users/upload/", status_code=status.HTTP_201_CREATED)
async def upload_users(file: UploadFile = File(..., description="Arquivo TXT/CSV com usuários (formato: nome,idade por linha)")):
    """
    Processa um arquivo TXT/CSV, lê os usuários e os insere em massa no MongoDB.
    """
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Serviço de Banco de Dados Indisponível")

    try:
        contents = await file.read()
        s = str(contents, 'utf-8')
        data = io.StringIO(s)
        
        reader = csv.reader(data, delimiter=',')
        users_to_insert = []
        
        for row in reader:
            if len(row) == 2:
                nome = row[0].strip()
                idade_str = row[1].strip()
                
                try:
                    # Valida e formata os dados usando o modelo Pydantic
                    user_doc = UserCreate(nome=nome, idade=int(idade_str))
                    users_to_insert.append(user_doc.model_dump())
                    
                except Exception:
                    # Ignora linhas inválidas
                    continue

        if not users_to_insert:
            raise HTTPException(status_code=400, detail="Nenhum dado válido de usuário encontrado no arquivo.")

        # Insere os documentos em massa
        result = await users_collection.insert_many(users_to_insert)

        return {
            "message": f"Upload e Inserção em massa concluída.",
            "inserted_count": len(result.inserted_ids),
            "total_records_processed": len(users_to_insert)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante o processamento do arquivo: {e}")