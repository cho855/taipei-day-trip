

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app import app as static_app  # 引入 app.py 裡的 app
import mysql.connector
import json
from typing import Optional, List



app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(static_app.router)



DB_HOST = "localhost"
DB_USER = "root"          
DB_PASSWORD = "abc6788"   
DB_NAME = "taipei_trip"  


def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Exception as e:
        print(" MySQL 連線錯誤：", e)
        raise


# =========================================================
# 三、小工具：把 images 欄位轉成 Python list
# =========================================================

def parse_images(images_value):

    if images_value is None:
        return []

    if isinstance(images_value, list):
        return images_value

    try:
        return json.loads(images_value)
    except Exception:
        return []


@app.get("/api/attractions")
def get_attractions(
    page: int = 0,
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    page_size = 12

    if page < 0:
        page = 0

    offset = page * page_size

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params: List = []

    if keyword:
        where_clauses.append("(name LIKE %s OR description LIKE %s)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])

    if category:
        where_clauses.append("category = %s")
        params.append(category)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT
            id,
            name,
            category,
            description,
            address,
            transport,
            mrt,
            latitude,
            longitude,
            images
        FROM attraction
        {where_sql}
        LIMIT %s OFFSET %s
    """

    params.extend([page_size, offset])

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    attractions = []
    for row in rows:
        attractions.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "description": row["description"],
            "address": row["address"],
            "transport": row["transport"],
            "mrt": row["mrt"],
            "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
            "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
            "images": parse_images(row["images"]),
        })

    next_page = page + 1 if len(attractions) == page_size else None

    cursor.close()
    conn.close()

    return {
        "nextPage": next_page,
        "data": attractions
    }




@app.get("/api/attraction/{attraction_id}")
def get_attraction(attraction_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            id,
            name,
            category,
            description,
            address,
            transport,
            mrt,
            latitude,
            longitude,
            images
        FROM attraction
        WHERE id = %s
    """
    cursor.execute(sql, [attraction_id])
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "景點編號不正確"
            }
        )

    data = {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "address": row["address"],
        "transport": row["transport"],
        "mrt": row["mrt"],
        "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
        "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
        "images": parse_images(row["images"]),
    }

    return {
        "data": data
    }




@app.get("/api/categories")
def get_categories():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT category
        FROM attraction
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    categories = [row[0] for row in rows]

    return {
        "data": categories
    }




@app.get("/api/mrts")
def get_mrts():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT mrt, id, name
        FROM attraction
        WHERE mrt IS NOT NULL AND mrt != ''
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    mrt_map = {}

    for row in rows:
        mrt_name = row["mrt"]
        if mrt_name not in mrt_map:
            mrt_map[mrt_name] = []
        mrt_map[mrt_name].append({
            "id": row["id"],
            "name": row["name"]
        })


    sorted_mrts = sorted(
        mrt_map.items(),
        key=lambda item: len(item[1]),
        reverse=True
    )

    result = []
    for mrt_name, stations in sorted_mrts:
        result.append({
            "mrt": mrt_name,
            "stations": stations
        })

    return {
        "data": result
    }
