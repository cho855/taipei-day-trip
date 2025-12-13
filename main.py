from typing import Optional, List

import mysql.connector
from fastapi import Query
from fastapi.responses import JSONResponse

from app import app


DB_HOST = "localhost"
DB_USER = "tripuser"
DB_PASSWORD = "abc6788"
DB_NAME = "taipei_trip"

PAGE_SIZE = 8  


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def error_response(status_code: int):
    return JSONResponse(
        content={"error": True, "message": "請按照情境提供對應的錯誤訊息"},
        status_code=status_code,
    )


def row_to_attraction(row: dict) -> dict:
    images_value = row.get("images")

    if images_value is not None and str(images_value).strip() != "":
        images = str(images_value).split(",")
    else:
        images = []

    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "address": row["address"],
        "transport": row["transport"],
        "mrt": row["mrt"],
        "lat": row["latitude"],
        "lng": row["longitude"],
        "images": images,
    }



# 1. GET /api/attractions
@app.get("/api/attractions")
def get_attractions(
    page: int = Query(0, ge=0),
    category: Optional[str] = None,  
    keyword: Optional[str] = None,   
):
    try:
        offset = page * PAGE_SIZE

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM attraction"
        params: List[object] = []
        has_where = False


        if category is not None and category.strip() != "":
            cat = category.strip()

            if not has_where:
                sql += " WHERE "
                has_where = True
            else:
                sql += " AND "

            sql += "category = %s"
            params.append(cat)


        if keyword is not None and keyword.strip() != "":
            kw_raw = keyword.strip()
            kw_like = "%" + kw_raw + "%"

            if not has_where:
                sql += " WHERE "
                has_where = True
            else:
                sql += " AND "

            sql += "(name LIKE %s OR mrt = %s)"
            params.append(kw_like)
            params.append(kw_raw)


        sql += " ORDER BY id LIMIT %s OFFSET %s"
        params.append(PAGE_SIZE + 1)
        params.append(offset)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        conn.close()

        if len(rows) > PAGE_SIZE:
            next_page = page + 1
            rows = rows[:PAGE_SIZE]
        else:
            next_page = None

        data = []
        for r in rows:
            data.append(row_to_attraction(r))

        return {"nextPage": next_page, "data": data}

    except Exception:
        return error_response(500)



# 2. GET /api/attraction/{attractionId}
@app.get("/api/attraction/{attractionId}")
def get_attraction(attractionId: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM attraction WHERE id = %s", (attractionId,))
        row = cursor.fetchone()

        conn.close()

        if row is None:
            return error_response(400)

        return {"data": row_to_attraction(row)}

    except Exception:
        return error_response(500)



# 3. GET /api/categories

@app.get("/api/categories")
def get_categories():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT DISTINCT category FROM attraction "
            "WHERE category IS NOT NULL AND category != '' "
            "ORDER BY category"
        )
        rows = cursor.fetchall()
        conn.close()

        categories = []
        for r in rows:
            categories.append(r["category"])

        return {"data": categories}

    except Exception:
        return error_response(500)



# 4. GET /api/mrts
@app.get("/api/mrts")
def get_mrts():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT mrt, COUNT(*) AS count
            FROM attraction
            WHERE mrt IS NOT NULL AND mrt != ''
            GROUP BY mrt
            ORDER BY count DESC, mrt ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        mrts = []
        for r in rows:
            mrts.append(r["mrt"])

        return {"data": mrts}

    except Exception:
        return error_response(500)
