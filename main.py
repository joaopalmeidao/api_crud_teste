from fastapi.middleware.cors import CORSMiddleware 
from pyngrok import ngrok # Permite o acesso remoto da aplicação local.
from pydantic import BaseModel
from typing import List
import sqlite3
from sqlite3 import Error
from fastapi import FastAPI, HTTPException
import uvicorn


'''
Métodos do protocolo HTTP (CRUD):
POST: criar (enviar) dados no servidor (create).
GET: ler dados (read).
PUT: atualizar dados no servidor (update).
DELETE: remover dados no servidor (delete)
'''

database_name = 'database.sqlite3'
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class Item(BaseModel):
    nome: str
    descricao: str | None
    preco: float
    imposto: float | None
    categorias: List[str] | None

def get_db():
    conn = sqlite3.connect(database_name)
    return conn

def create_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id integer primary key autoincrement,
            nome varchar(250) not null,
            descricao varchar(1000) not null,
            preco real,
            imposto real,
            categorias varchar(250)
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup():
    create_table()

@app.get("/")
async def cumprimentar():
    return {"mensagem": "Olá, Mundo!"}

@app.post("/body/itens")
async def criar_item(item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO produtos (nome, descricao, preco, imposto, categorias)
        VALUES (?, ?, ?, ?, ?)
    ''', (item.nome, item.descricao, item.preco, item.imposto, str(item.categorias).replace("'",'"')))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, **item.dict()}

@app.get("/itens/{item_id}")
async def ler_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (item_id,))
    row = cursor.fetchone()
    colunas = list(i[0] for i in cursor.description)
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(zip(colunas,row))

@app.put("/itens/{item_id}")
async def atualizar_item(item_id: int, item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE produtos SET
        nome = ?,
        descricao = ?,
        preco = ?,
        imposto = ?,
        categorias = ?
        WHERE id = ?
    ''', (item.nome, item.descricao, item.preco, item.imposto, str(item.categorias).replace("'",'"'), item_id))
    conn.commit()
    conn.close()
    return {"mensagem": "Item atualizado com sucesso"}

@app.delete("/itens/{item_id}")
async def remover_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM produtos WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return {"mensagem": "Item removido com sucesso"}


if __name__ == "__main__":
    ngrok_tunnel = ngrok.connect(8000)
    print('Public URL:', ngrok_tunnel.public_url)
    uvicorn.run(app, port=8000,host='0.0.0.0')
