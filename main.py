from typing import Optional, List
from fastapi import Query, FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
import json
import mysql.connector

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

#/attraction/{id}
@app.get("/attraction/{attractionId}")
def read_attraction(attractionId: int):
    return FileResponse("static/attraction.html")


DB_HOST = "localhost"
DB_USER = "tripuser"
DB_PASSWORD = "abc6788"
DB_NAME = "taipei_trip"

PAGE_SIZE = 8


###part4
# JWT / Password 
JWT_SECRET = "987654321"
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)


def create_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])


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


###part4
def get_user_from_bearer(request: Request) -> Optional[dict]:
    auth = request.headers.get("Authorization")
    if not auth:
        return None

    prefix = "Bearer "
    if not auth.startswith(prefix):
        return None

    token = auth[len(prefix):].strip()
    if token == "":
        return None

    try:
        payload = decode_token(token)
        return payload
    except Exception:
        return None


def row_to_attraction(row: dict) -> dict:
    images_value = row.get("images")

    if images_value is None:
        images = []
    elif isinstance(images_value, list):
        images = images_value
    elif isinstance(images_value, (bytes, bytearray)):
        images = json.loads(images_value.decode("utf-8"))
    elif isinstance(images_value, str):
        images = json.loads(images_value)
    else:
        images = json.loads(str(images_value))

    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "address": row["address"],
        "transport": row["transport"],
        "mrt": row["mrt"],
        "lat": float(row["latitude"]) if row["latitude"] is not None else None,
        "lng": float(row["longitude"]) if row["longitude"] is not None else None,
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

            sql += "(name LIKE %s OR mrt LIKE %s)"
            params.append(kw_like)
            params.append(kw_like)  

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

    except Exception as e:
        import traceback
        print("\n==== ERROR /api/attractions ====")
        print("Exception:", repr(e))
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return error_response(500)


# part4===== Request Bodies =====
class SignupBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class SigninBody(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


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

    except Exception as e:
        import traceback
        print("\n==== ERROR /api/attraction/{id} ====")
        print("Exception:", repr(e))
        traceback.print_exc()
        print("==== END ERROR ====\n")
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

    except Exception as e:
        print("ERROR /api/categories:", repr(e))
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

    except Exception as e:
        print("ERROR /api/mrts:", repr(e))
        return error_response(500)


#part4
# 1) Sign Up: POST /api/user
@app.post("/api/user")
def signup(body: SignupBody):
    conn = None  
    try:
        name = (body.name or "").strip()
        email = (body.email or "").strip().lower()
        password = (body.password or "").strip()

        if name == "" or email == "" or password == "":
            return JSONResponse(
                content={"error": True, "message": "註冊欄位不可空白"},
                status_code=400,
            )

        if len(password.encode("utf-8")) > 72:
            return JSONResponse(
                content={"error": True, "message": "密碼過長"},
                status_code=400,
            )

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM member WHERE email = %s", (email,))
        existed = cursor.fetchone()
        if existed is not None:
            return JSONResponse(
                content={"error": True, "message": "Email 已被註冊"},
                status_code=400,
            )

        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO member (name, email, password) VALUES (%s, %s, %s)",
            (name, email, pw_hash),
        )
        conn.commit()

        return {"ok": True}

    except Exception:
        import traceback
        print("\n==== ERROR POST /api/user ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return JSONResponse(
            content={"error": True, "message": "伺服器內部錯誤"},
            status_code=500,
        )
    finally:
        if conn is not None:
            conn.close()


# 2) Sign In: PUT /api/user/auth
@app.put("/api/user/auth")
def signin(body: SigninBody):
    conn = None  
    try:
        email = (body.email or "").strip().lower()
        password = (body.password or "").strip()

        if email == "" or password == "":
            return JSONResponse(
                content={"error": True, "message": "請輸入 Email 與密碼"},
                status_code=400,
            )

        if len(password.encode("utf-8")) > 72:
            return JSONResponse(
                content={"error": True, "message": "帳號或密碼錯誤"},
                status_code=400,
            )

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, password FROM member WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()

        if user is None:
            return JSONResponse(
                content={"error": True, "message": "帳號或密碼錯誤"},
                status_code=400,
            )

        if not verify_password(password, user["password"]):
            return JSONResponse(
                content={"error": True, "message": "帳號或密碼錯誤"},
                status_code=400,
            )

        token = create_token(
            {"id": user["id"], "name": user["name"], "email": user["email"]}
        )
        return {"token": token}

    except Exception:
        import traceback
        print("\n==== ERROR PUT /api/user/auth ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return JSONResponse(
            content={"error": True, "message": "伺服器內部錯誤"},
            status_code=500,
        )
    finally:
        if conn is not None:
            conn.close()


# 3) Get current user: GET /api/user/auth
@app.get("/api/user/auth")
def get_current_user(request: Request):
    payload = get_user_from_bearer(request)
    if payload is None:
        return {"data": None}

    user_id = payload.get("id")
    if user_id is None:
        return {"data": None}

    conn = None  
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM member WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user is None:
            return {"data": None}

        return {"data": {"id": user["id"], "name": user["name"], "email": user["email"]}}

    except Exception:
        import traceback
        print("\n==== ERROR GET /api/user/auth ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return JSONResponse(
            content={"error": True, "message": "伺服器內部錯誤"},
            status_code=500,
        )
    finally:
        if conn is not None:
            conn.close()
