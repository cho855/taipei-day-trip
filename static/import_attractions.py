import os
import json
import re
import mysql.connector


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
json_path = os.path.join(BASE_DIR, "..", "data", "taipei-attractions.json")

print("Loading JSON from:", json_path)


with open(json_path, "r", encoding="utf-8") as f:
    raw = json.load(f)


conn = mysql.connector.connect(
    host="localhost",
    user="tripuser",          
    password="abc6788",   
    database="taipei_trip"  
)
cursor = conn.cursor()


pattern = re.compile(r"https?://[^\s]+?\.(?:jpg|JPG|png|PNG)")


for item in raw["result"]["results"]:
   
    at_id = int(item["_id"])          
    name = item["name"]               
    category = item["CAT"]            
    description = item["description"] 
    address = item["address"]         
    transport = item["direction"]     
    mrt = item.get("MRT")             

    lat = float(item["latitude"])     
    lng = float(item["longitude"])


    file_str = item["file"]
    image_urls = pattern.findall(file_str)


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


conn.commit()
cursor.close()
conn.close()

print("Done! All attractions imported.")
