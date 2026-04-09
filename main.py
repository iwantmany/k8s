from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "haproxy.postgres-ha.svc.cluster.local"),
    "port": int(os.getenv("DB_PORT", 5000)),
    "database": os.getenv("DB_NAME", "testdb"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "SuperPass!2024"),
    "sslmode": "require"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

class UserCreate(BaseModel):
    name: str

@app.get("/")
def health():
    return {"status": "ok", "message": "k8s-app v2.0 running"}

@app.get("/users")
def get_users():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM users ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"users": [{"id": r[0], "name": r[1], "created_at": str(r[2])} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users")
def create_user(user: UserCreate):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (user.name,))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"id": user_id, "name": user.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
