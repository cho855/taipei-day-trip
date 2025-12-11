import os
import json
import re
import mysql.connector

# 1. 找到 taipei-attractions.json 的路徑
#    目前這支程式放在 static/ 底下，所以回到上一層再進 data/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # static/
json_path = os.path.join(BASE_DIR, "..", "data", "taipei-attractions.json")

print("Loading JSON from:", json_path)

# 2. 讀取 JSON 檔
with open(json_path, "r", encoding="utf-8") as f:
    raw = json.load(f)

# 3. 連線到 MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",          # 這裡改成你的 MySQL 帳號
    password="Asd96601123!!!",   # 這裡改成你的 MySQL 密碼
    database="taipei_trip"  # 剛剛建立的資料庫名稱
)
cursor = conn.cursor()

# 如果你想每次重跑匯入前把舊資料清空，可以打開下面這兩行
# print("Truncating table attraction ...")
# cursor.execute("TRUNCATE TABLE attraction")

# 4. 準備一個正則表達式，把 file 字串裡的 jpg/png 圖片網址抓出來
pattern = re.compile(r"https?://[^\s]+?\.(?:jpg|JPG|png|PNG)")

# 5. 走訪每一個景點資料
for item in raw["result"]["results"]:
    # 對應欄位：從 JSON 抓資料出來
    at_id = int(item["_id"])          # 表裡的 id
    name = item["name"]               # 景點名稱
    category = item["CAT"]            # 類別
    description = item["description"] # 景點介紹
    address = item["address"]         # 地址
    transport = item["direction"]     # 如何到達
    mrt = item.get("MRT")             # 捷運站，有些可能是 None

    lat = float(item["latitude"])     # 經緯度轉成 float
    lng = float(item["longitude"])

    # 從 file 那一長串裡抓出所有 jpg/png 結尾的網址
    file_str = item["file"]
    image_urls = pattern.findall(file_str)

    # 轉成 JSON 字串存進資料庫（對應 images 欄位）
    images_json = json.dumps(image_urls, ensure_ascii=False)

    sql = """
        INSERT INTO attraction
        (id, name, category, description, address, transport, mrt, latitude, longitude, images)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        at_id, name, category, description,
        address, transport, mrt, lat, lng, images_json
    )

    cursor.execute(sql, params)

# 6. 寫入資料庫 & 關閉連線
conn.commit()
cursor.close()
conn.close()

print("Done! All attractions imported.")
