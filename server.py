from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import uvicorn

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLiteデータベースの初期設定
def init_db():
    with sqlite3.connect("travel_plans.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day INTEGER NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL,
            transport TEXT NOT NULL,
            cost INTEGER NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            cost INTEGER NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )""")

# データベースの初期化
init_db()

# Pydanticモデル定義
class Place(BaseModel):
    day: int
    time: str
    location: str
    transport: str
    cost: int

class WishlistItem(BaseModel):
    item_name: str
    cost: int

# Todoモデル定義
class Todo(BaseModel):
    title: str  # TODOのタイトル（必須）
    completed: Optional[bool] = False  # 完了状態（省略可能、デフォルトは未完了）

# Todoレスポンスモデル（IDを含む）
class TodoResponse(Todo):
    id: int  # TODOのID

@app.get("/places", response_model=List[Place])
def get_places():
    with sqlite3.connect("travel_plans.db") as conn:
        places = conn.execute("SELECT * FROM places ORDER BY day, time").fetchall()
        return [{"id": row[0], "day": row[1], "time": row[2], "location": row[3], "transport": row[4], "cost": row[5]} for row in places]

@app.post("/places", response_model=Place)
def add_place(place: Place):
    with sqlite3.connect("travel_plans.db") as conn:
        cursor = conn.execute(
            "INSERT INTO places (day, time, location, transport, cost) VALUES (?, ?, ?, ?, ?)",
            (place.day, place.time, place.location, place.transport, place.cost),
        )
        place_id = cursor.lastrowid
        return {**place.dict(), "id": place_id}

@app.get("/wishlist", response_model=List[WishlistItem])
def get_wishlist():
    with sqlite3.connect("travel_plans.db") as conn:
        wishlist = conn.execute("SELECT * FROM wishlist").fetchall()
        return [{"id": row[0], "item_name": row[1], "cost": row[2]} for row in wishlist]

@app.post("/wishlist", response_model=WishlistItem)
def add_wishlist_item(item: WishlistItem):
    with sqlite3.connect("travel_plans.db") as conn:
        cursor = conn.execute(
            "INSERT INTO wishlist (item_name, cost) VALUES (?, ?)",
            (item.item_name, item.cost),
        )
        item_id = cursor.lastrowid
        return {**item.dict(), "id": item_id}
    
        # 合計金額の取得
@app.get("/total_cost")
def get_total_cost():
    with sqlite3.connect("travel_plans.db") as conn:
        places_cost = conn.execute("SELECT SUM(cost) FROM places").fetchone()[0] or 0
        wishlist_cost = conn.execute("SELECT SUM(cost) FROM wishlist").fetchone()[0] or 0
        total_cost = places_cost + wishlist_cost
        return {"total_cost": total_cost}



# TODOの取得
@app.get("/todos", response_model=List[TodoResponse])
def get_todos():
    with sqlite3.connect("travel_plans.db") as conn:
        todos = conn.execute("SELECT * FROM todos").fetchall()
        return [{"id": row[0], "title": row[1], "completed": bool(row[2])} for row in todos]

# TODOの追加
@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: Todo):
    with sqlite3.connect("travel_plans.db") as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title, completed) VALUES (?, ?)",
            (todo.title, todo.completed),
        )
        todo_id = cursor.lastrowid
        return {"id": todo_id, "title": todo.title, "completed": todo.completed}

# TODOの更新
@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: Todo):
    with sqlite3.connect("travel_plans.db") as conn:
        cursor = conn.execute(
            "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
            (todo.title, todo.completed, todo_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"id": todo_id, "title": todo.title, "completed": todo.completed}

# TODOの削除
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    with sqlite3.connect("travel_plans.db") as conn:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"message": "Todo deleted"}

# クライアント用のHTMLを返すエンドポイント
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("client.html", "r", encoding="utf-8") as f:
        return f.read()

# サーバーを起動するためのコード
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

