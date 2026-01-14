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
import os
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/thankyou")
def read_thankyou():
    return FileResponse("static/thankyou.html")




@app.get("/")
def read_index():
    return FileResponse("static/index.html")


@app.get("/attraction/{attractionId}")
def read_attraction(attractionId: int):
    return FileResponse("static/attraction.html")


# Part 5-2 Booking Page Layout: /booking
@app.get("/booking")
def read_booking():
    return FileResponse("static/booking.html")


DB_HOST = "localhost"
DB_USER = "tripuser"
DB_PASSWORD = "abc6788"
DB_NAME = "taipei_trip"

PAGE_SIZE = 8


# Part 4 JWT / Password

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


def parse_images(images_value) -> list:
    if images_value is None:
        return []
    if isinstance(images_value, list):
        return images_value
    if isinstance(images_value, (bytes, bytearray)):
        return json.loads(images_value.decode("utf-8"))
    if isinstance(images_value, str):
        return json.loads(images_value)
    return json.loads(str(images_value))


def row_to_attraction(row: dict) -> dict:
    images = parse_images(row.get("images"))

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


#  Part 2 APIs
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


class SignupBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class SigninBody(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


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


#  Part 4 User APIs
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


# Part 5 Booking 

class BookingBody(BaseModel):
    attractionId: Optional[int] = None
    date: Optional[str] = None
    time: Optional[str] = None
    price: Optional[int] = None


@app.get("/api/booking")
def get_booking(request: Request):
    payload = get_user_from_bearer(request)
    if payload is None or payload.get("id") is None:
        return error_response(403)

    user_id = payload["id"]

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT member_id, attraction_id, date, time, price FROM booking WHERE member_id = %s",
            (user_id,),
        )
        b = cursor.fetchone()

        if b is None:
            return {"data": None}

        cursor.execute(
            "SELECT id, name, address, images FROM attraction WHERE id = %s",
            (b["attraction_id"],),
        )
        a = cursor.fetchone()

      
        if a is None:
            return {"data": None}

        image = ""
        try:
            imgs = json.loads(a["images"]) if a.get("images") else []
            if isinstance(imgs, list) and len(imgs) > 0:
                image = imgs[0]
        except Exception:
            image = ""

        return {
            "data": {
                "attraction": {
                    "id": a["id"],
                    "name": a["name"],
                    "address": a["address"],
                    "image": image,
                },
                "date": str(b["date"]),
                "time": b["time"],
                "price": b["price"],
            }
        }

    except Exception:
        import traceback
        print("\n==== ERROR GET /api/booking ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return error_response(500)
    finally:
        if conn is not None:
            conn.close()


@app.post("/api/booking")
def create_or_replace_booking(body: BookingBody, request: Request):
    payload = get_user_from_bearer(request)
    if payload is None or payload.get("id") is None:
        return error_response(403)

    user_id = payload["id"]

    attraction_id = body.attractionId
    date = (body.date or "").strip()
    time = (body.time or "").strip()
    price = body.price


    if attraction_id is None or date == "" or time == "" or price is None:
        return error_response(400)

    if time not in ["morning", "afternoon"]:
        return error_response(400)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)


        cursor.execute("SELECT id FROM attraction WHERE id = %s", (attraction_id,))
        a = cursor.fetchone()
        if a is None:
            return error_response(400)


        cursor.execute("SELECT member_id FROM booking WHERE member_id = %s", (user_id,))
        existed = cursor.fetchone()

        if existed is None:
            cursor.execute(
                "INSERT INTO booking (member_id, attraction_id, date, time, price) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, attraction_id, date, time, price),
            )
        else:
            cursor.execute(
                "UPDATE booking SET attraction_id = %s, date = %s, time = %s, price = %s "
                "WHERE member_id = %s",
                (attraction_id, date, time, price, user_id),
            )

        conn.commit()
        return {"ok": True}

    except Exception:
        import traceback
        print("\n==== ERROR POST /api/booking ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return error_response(500)
    finally:
        if conn is not None:
            conn.close()


@app.delete("/api/booking")
def delete_booking(request: Request):
    payload = get_user_from_bearer(request)
    if payload is None or payload.get("id") is None:
        return error_response(403)

    user_id = payload["id"]

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM booking WHERE member_id = %s", (user_id,))
        conn.commit()

        return {"ok": True}

    except Exception:
        import traceback
        print("\n==== ERROR DELETE /api/booking ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return error_response(500)
    finally:
        if conn is not None:
            conn.close()


# Part 6 Order APIs


TAPPAY_PARTNER_KEY = os.getenv("TAPPAY_PARTNER_KEY", "").strip()
TAPPAY_MERCHANT_ID = os.getenv("TAPPAY_MERCHANT_ID", "").strip()
TAPPAY_PAY_BY_PRIME_URL = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"  


class ContactBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class OrderCreateBody(BaseModel):
    prime: Optional[str] = None
    contact: Optional[ContactBody] = None


def gen_order_number() -> str:    
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    micro = datetime.now(timezone.utc).strftime("%f")
    return f"{now}{micro}"


@app.post("/api/orders")
async def create_order(body: OrderCreateBody, request: Request):   
    payload = get_user_from_bearer(request)
    if payload is None or payload.get("id") is None:
        return error_response(403)

    user_id = payload["id"]


    prime = (body.prime or "").strip()
    if prime == "":
        return JSONResponse(
            content={"error": True, "message": "Prime 不可為空"},
            status_code=400,
        )

    contact = body.contact or ContactBody()
    contact_name = (contact.name or "").strip()
    contact_email = (contact.email or "").strip()
    contact_phone = (contact.phone or "").strip()

    if contact_name == "" or contact_email == "" or contact_phone == "":
        return JSONResponse(
            content={"error": True, "message": "聯絡資訊不可空白"},
            status_code=400,
        )

  
    if TAPPAY_PARTNER_KEY == "" or TAPPAY_MERCHANT_ID == "":
        return JSONResponse(
            content={"error": True, "message": "TapPay 金鑰未設定（TAPPAY_PARTNER_KEY / TAPPAY_MERCHANT_ID）"},
            status_code=500,
        )

    conn = None
    order_number = gen_order_number()

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)


        cursor.execute(
            "SELECT member_id, attraction_id, date, time, price FROM booking WHERE member_id = %s",
            (user_id,),
        )
        b = cursor.fetchone()

        if b is None:
            return JSONResponse(
                content={"error": True, "message": "目前沒有待預訂行程"},
                status_code=400,
            )

        
        cursor.execute(
            """
            INSERT INTO orders
              (order_number, member_id, attraction_id, date, time, price,
               contact_name, contact_email, contact_phone, status)
            VALUES
              (%s, %s, %s, %s, %s, %s,
               %s, %s, %s, 'UNPAID')
            """,
            (
                order_number,
                user_id,
                b["attraction_id"],
                b["date"],
                b["time"],
                b["price"],
                contact_name,
                contact_email,
                contact_phone,
            ),
        )
        conn.commit()

       
        tappay_req = {
            "prime": prime,
            "partner_key": TAPPAY_PARTNER_KEY,
            "merchant_id": TAPPAY_MERCHANT_ID,
            "details": "Taipei Day Trip Order",
            "amount": int(b["price"]),
            "cardholder": {
                "phone_number": contact_phone,
                "name": contact_name,
                "email": contact_email,
            },
            "remember": False,
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": TAPPAY_PARTNER_KEY,  
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(TAPPAY_PAY_BY_PRIME_URL, json=tappay_req, headers=headers)
            tappay_data = resp.json()

        tappay_status = int(tappay_data.get("status", -999))
        tappay_msg = str(tappay_data.get("msg", ""))
        rec_trade_id = tappay_data.get("rec_trade_id")
        bank_transaction_id = tappay_data.get("bank_transaction_id")

 
        cursor.execute(
            """
            INSERT INTO payments
              (order_number, tappay_status, tappay_msg, rec_trade_id, bank_transaction_id, raw_json)
            VALUES
              (%s, %s, %s, %s, %s, %s)
            """,
            (
                order_number,
                tappay_status,
                tappay_msg[:255],
                rec_trade_id,
                bank_transaction_id,
                json.dumps(tappay_data, ensure_ascii=False),
            ),
        )

       
        if tappay_status == 0:
            cursor.execute(
                "UPDATE orders SET status = 'PAID' WHERE order_number = %s",
                (order_number,),
            )
           
            cursor.execute("DELETE FROM booking WHERE member_id = %s", (user_id,))

        conn.commit()


        return {
            "data": {
                "number": order_number,
                "payment": {
                    "status": tappay_status,
                    "message": tappay_msg,
                },
            }
        }

    except Exception:
        import traceback
        print("\n==== ERROR POST /api/orders ====")
        traceback.print_exc()
        print("==== END ERROR ====\n")
        return JSONResponse(
            content={"error": True, "message": "伺服器內部錯誤"},
            status_code=500,
        )
    finally:
        if conn is not None:
            conn.close()
