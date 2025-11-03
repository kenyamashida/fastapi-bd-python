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

# 1. Modelo de Criação (POST /users/)
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

# 2. Modelo de Atualização (PUT /users/{id})
class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3)
    idade: Optional[int] = Field(None, gt=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Carla Oliveira",
                "idade": 29
            }
        }
    }


# 3. Modelo de Saída (Retorno de GET/POST/PUT)
class UserDB(BaseModel):
    # 'id' aceita qualquer tipo na entrada (ObjectId) mas é serializado como string
    id: Optional[Any] = Field(alias="_id", default=None) 
    nome: str
    idade: int

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True, 
        "json_encoders": {ObjectId: str}, # Força ObjectId a ser serializado como string JSON
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
        # Se falhar no startup, garante que o erro seja visível
        raise RuntimeError("MONGO_URI não configurado no .env")

    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        users_collection = db[COLLECTION_NAME]
        
        await client.admin.command('ping') 
        print("✅ Conectado com sucesso ao MongoDB!")

    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB. Detalhe: {e}")
        raise RuntimeError(f"Falha na inicialização da conexão com o DB: {e}")

        
@app.on_event("shutdown")
async def shutdown_db_client():
    """Fecha a conexão com o MongoDB ao desligar o FastAPI."""
    global client
    if client:
        client.close()
        print("🔌 Conexão com MongoDB fechada.")

# --- 4. ENDPOINTS DO CRUD ---

# Helper para checagem rápida da conexão
def check_db_connection():
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Serviço de Banco de Dados Indisponível")

# --- CREATE (C) ---
@app.post("/users/", response_model=UserDB, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Cria um novo usuário."""
    check_db_connection()
        
    user_data = user.model_dump() 
    insert_result = await users_collection.insert_one(user_data)
    
    created_user = await users_collection.find_one({"_id": insert_result.inserted_id})
    
    # Serialização manual para garantir que o Pydantic não trave
    created_user['id'] = str(created_user.pop('_id'))
    
    return created_user

# --- READ (R) ---

## Listar Todos
@app.get("/users/", response_model=List[UserDB])
async def list_users():
    """Retorna todos os usuários."""
    check_db_connection()

    users = [] 
    
    async for document in users_collection.find():
        # Serialização manual do _id antes da validação Pydantic
        document['id'] = str(document.pop('_id'))
        users.append(UserDB.model_validate(document)) 
        
    return users

## Buscar por ID
@app.get("/users/{id}", response_model=UserDB)
async def get_user(id: str):
    """Busca um único usuário pelo ID."""
    check_db_connection()
    
    try:
        user_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    user_document = await users_collection.find_one({"_id": user_id})

    if user_document:
        # Serializa e retorna
        user_document['id'] = str(user_document.pop('_id'))
        return user_document
    
    raise HTTPException(status_code=404, detail=f"Usuário com ID {id} não encontrado")


# --- UPDATE (U) ---
@app.put("/users/{id}", response_model=UserDB)
async def update_user(id: str, user_update: UserUpdate):
    """Atualiza um usuário existente pelo ID."""
    check_db_connection()
        
    try:
        user_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    update_data = user_update.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualização fornecido")

    update_result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )

    if update_result.modified_count == 1:
        updated_document = await users_collection.find_one({"_id": user_id})
        
        # Serializa e retorna
        updated_document['id'] = str(updated_document.pop('_id'))
        return updated_document
    
    # Se o documento não foi encontrado para atualização
    raise HTTPException(status_code=404, detail=f"Usuário com ID {id} não encontrado")


# --- DELETE (D) ---
@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: str):
    """Exclui um usuário do MongoDB pelo ID."""
    check_db_connection()
        
    try:
        user_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    delete_result = await users_collection.delete_one({"_id": user_id})

    if delete_result.deleted_count == 1:
        return status.HTTP_204_NO_CONTENT
    
    raise HTTPException(status_code=404, detail=f"Usuário com ID {id} não encontrado")


# --- ENDPOINT DE UPLOAD (BÔNUS) ---

@app.post("/users/upload/", status_code=status.HTTP_201_CREATED)
async def upload_users(file: UploadFile = File(..., description="Arquivo TXT/CSV com usuários")):
    """Processa um arquivo CSV e os insere em massa no MongoDB."""
    check_db_connection()

    try:
        contents = await file.read()
        s = str(contents, 'utf-8')
        data = io.StringIO(s)
        
        reader = csv.reader(data, delimiter=',')
        users_to_insert = []
        
        for row in reader:
            if len(row) == 2:
                # Usa o modelo UserCreate para validação automática dos dados lidos
                user_doc = UserCreate(nome=row[0].strip(), idade=int(row[1].strip()))
                users_to_insert.append(user_doc.model_dump())
                    
        if not users_to_insert:
            raise HTTPException(status_code=400, detail="Nenhum dado válido de usuário encontrado no arquivo.")

        result = await users_collection.insert_many(users_to_insert)

        return {
            "message": f"Upload e Inserção em massa concluída.",
            "inserted_count": len(result.inserted_ids),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante o processamento do arquivo: {e}")