from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import uvicorn

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI()

# CORSを有効化（開発時のみ）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
    expose_headers=["*"]
)

# データベース関連の定数
DATABASE_NAME = "travel_todos.db"
TABLE_NAME = "travel_todos"

# データベース接続のヘルパー関数
def get_db():
    """
    データベース接続を提供する
    例外が発生した場合はHTTPExceptionを発生させる
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(
            status_code=500,
            detail="データベース接続エラー"
        )

# データベースの初期設定を行う関数
def init_db():
    """
    データベースとテーブルの初期化を行う
    テーブルが存在しない場合は新規作成する
    """
    with get_db() as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                destination TEXT NOT NULL,
                location TEXT NOT NULL,
                starttime TEXT NOT NULL,
                totaltime TEXT NOT NULL,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0
            )
        """)

# リクエストボディのデータ構造を定義するクラス
class TravelTodo(BaseModel):
    """
    旅行プランTODOのデータモデル
    """
    date: str
    destination: str
    location: str
    starttime: str
    totaltime: str
    title: str
    completed: Optional[bool] = False

# レスポンスのデータ構造を定義するクラス
class TravelTodoResponse(TravelTodo):
    """
    旅行プランTODOのレスポンスモデル（IDを含む）
    """
    id: int

# 新規TODOを作成するエンドポイント
@app.post("/todos", response_model=TravelTodoResponse)
async def create_todo(todo: TravelTodo):
    """
    新しい旅行プランTODOを作成する
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                f"""
                INSERT INTO {TABLE_NAME} 
                (date, destination, location, starttime, totaltime, title, completed) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (todo.date, todo.destination, todo.location, todo.starttime, todo.totaltime,
                 todo.title, todo.completed)
            )
            conn.commit()
            todo_id = cursor.lastrowid
            return {
                "id": todo_id,
                "date": todo.date,
                "destination": todo.destination,
                "location": todo.location,
                "starttime": todo.starttime,
                "totaltime": todo.totaltime,
                "title": todo.title,
                "completed": todo.completed
            }
    except Exception as e:
        print(f"Error creating todo: {e}")
        raise HTTPException(
            status_code=500,
            detail="TODOの作成に失敗しました"
        )

# 全てのTODOを取得するエンドポイント
@app.get("/todos", response_model=List[TravelTodoResponse])
async def get_todos():
    """
    すべての旅行プランTODOを取得する
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY date")
            todos = cursor.fetchall()
            return [{
                "id": t[0],
                "date": t[1],
                "destination": t[2],
                "location": t[3],
                "starttime": t[4],
                "totaltime": t[5],
                "title": t[6],
                "completed": bool(t[7])
            } for t in todos]
    except Exception as e:
        print(f"Error getting todos: {e}")
        raise HTTPException(
            status_code=500,
            detail="TODOの取得に失敗しました"
        )

# TODOを削除するエンドポイント
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """
    指定されたIDの旅行プランTODOを削除する
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                f"DELETE FROM {TABLE_NAME} WHERE id = ?",
                (todo_id,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="指定されたTODOが見つかりません"
                )
            return {"message": "TODOを削除しました"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting todo: {e}")
        raise HTTPException(
            status_code=500,
            detail="TODOの削除に失敗しました"
        )

# HTMLを返すエンドポイント
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    クライアントのHTMLファイルを返す
    """
    try:
        with open("client.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        raise HTTPException(
            status_code=500,
            detail="HTMLファイルの読み込みに失敗しました"
        )

# サーバー起動用の関数
if __name__ == "__main__":
    import uvicorn
    init_db()  # データベースを初期化
    uvicorn.run(app, host="0.0.0.0", port=8000) 