import sqlite3
import csv
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rag.Semantic_for_DB import get_schema_and_context
from rag.vector_ingest import delete_vector_by_filename
class ImportRequest(BaseModel):
    filename: str
    table_name: str = "rag_table"

UPLOAD_DIR = os.path.join(os.path.dirname(__file__),"..", "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)
db_dir = os.path.join(os.path.dirname(__file__),"..","Data")
os.makedirs(db_dir, exist_ok=True)
DB_PATH = os.path.join(db_dir, "Data.db")
router = APIRouter()

def import_csv_to_sqlite(csv_filename, table_name="rag_table"):
    csv_path = os.path.join(UPLOAD_DIR, csv_filename)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        headers = next(reader)
        columns = ", ".join([f'"{h}" TEXT' for h in headers])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})')
        cursor.execute(f'DELETE FROM "{table_name}"')
        for row in reader:
            placeholders = ", ".join(["?"] * len(row))
            cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', row)
    conn.commit()
    conn.close()
    return True

@router.post("/import_csv_to_db/")
async def import_csv_to_db(req: ImportRequest):
    try:
        import_csv_to_sqlite(req.filename, req.table_name)
        get_schema_and_context(DB_PATH, save_json=True)  
        return JSONResponse({"status": "success"})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
    
import requests

@router.post("/delete_rag_file/")
async def delete_rag_file(data: dict):
    filename = data.get("filename")
    table_name = data.get("table_name")  
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file vật lý: {e}")
                return JSONResponse({"status": "error", "detail": f"Lỗi khi xóa file vật lý: {e}"}, status_code=500)
       
        if filename.endswith(".csv") or filename.endswith(".json"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
            except Exception as e:
                print(f"Lỗi khi lấy danh sách bảng: {e}")
                return JSONResponse({"status": "error", "detail": f"Lỗi khi lấy danh sách bảng: {e}"}, status_code=500)

          
            if not table_name:
                table_name = os.path.splitext(filename)[0]
            if table_name in tables:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    conn.commit()
                    conn.close()
                    print(f"Đã xóa bảng: {table_name}")
                except Exception as e:
                    print(f"Lỗi khi xóa bảng: {e}")
                    return JSONResponse({"status": "error", "detail": f"Lỗi khi xóa bảng: {e}"}, status_code=500)
            else:
                print(f"Không tìm thấy bảng {table_name} để xóa.")
            try:
                get_schema_and_context(DB_PATH, save_json=True)
            except Exception as e:
                print(f"Lỗi khi cập nhật schema/context: {e}")
        
        elif filename.endswith(".txt") or filename.endswith(".docx") or filename.endswith(".xlsx") or filename.endswith(".pdf") or filename.endswith(".json"):
            try:
                await delete_vector_by_filename({"filename": filename})
            except Exception as e:
                print(f"Lỗi khi gọi API xóa vector: {e}")
        else:
            try:
                get_schema_and_context(DB_PATH, save_json=True)
            except Exception as e:
                print(f"Lỗi khi cập nhật schema/context: {e}")
        return JSONResponse({"status": "success"})
    except Exception as e:
        print(f"Lỗi tổng quát khi xóa file: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)



@router.get("/list_db_tables/")
async def list_db_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return JSONResponse({"tables": tables})
    except Exception as e:
        
        return JSONResponse({"tables": [], "error": str(e)}, status_code=200)
@router.get("/get_table_data/")
async def get_table_data(table: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM "{table}" LIMIT 100')
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        return JSONResponse({"columns": columns, "rows": rows})
    except Exception as e:
        return JSONResponse({"columns": [], "rows": [], "error": str(e)}, status_code=500)
    

@router.get("/get_schema/")
async def get_schema_api():
    try:
        schema_context = get_schema_and_context(DB_PATH, save_json=True)
        return JSONResponse({"schema_context": schema_context})
    except Exception as e:
        return JSONResponse({"schema_context": [], "error": str(e)}, status_code=500)