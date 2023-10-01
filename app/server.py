from fastapi import FastAPI
import os
import subprocess
import requests
import sqlite3
from fastapi.staticfiles import StaticFiles
#from gpiozero import LED
import platform
import psutil
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import socket

app = FastAPI()
# CORS Configuration
origins = ["*"]  # This allows all origins. You can restrict it to specific origins if needed.

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can specify HTTP methods here
    allow_headers=["*"],  # You can specify HTTP headers here
)
# GPIO Pin used to trigger the relay
#trigger = LED(14)

# Create Table SQL
create_table_sql = """CREATE TABLE IF NOT EXISTS Favorites (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      channelId TEXT NOT NULL,
                      title TEXT NOT NULL,
                      location TEXT NOT NULL,
                      lng REAL NOT NULL,
                      lat REAL NOT NULL,
                      UNIQUE (channelId));"""

# if ./data/sqlite.db does not exist, create it
db_file = "./data/sqlite.db"
db_exists = os.path.exists(db_file)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

if not db_exists:
    cursor.execute(create_table_sql)
    print("New table Favorites created!")
else:
    print('Database "Favorites" ready to go!')

# Setup static files
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/channels/{locationId}")
async def get_channels(locationId: str):
    url = f"https://radio.garden/api/ara/content/page/{locationId}/channels"
    response = requests.get(url)
    json_data = response.json()
    channel_ids = [item['href'].split("/")[-1] for item in json_data['data']['content'][0]['items']]
    
    sql = f"SELECT channelId FROM Favorites WHERE channelId IN ({','.join(['?']*len(channel_ids))})"
    cursor.execute(sql, channel_ids)
    db_rows = cursor.fetchall()

    channel_id_lookup = set(row[0] for row in db_rows)

    for item in json_data['data']['content'][0]['items']:
        channel_id = item['href'].split("/")[-1]
        item['is_favorite'] = 1 if channel_id in channel_id_lookup else 0
    
    return json_data

@app.post("/addfavorite")
async def add_favorite(data: dict):
    channel_id = data['channelId']
    title = data['title']
    location = data['location']
    lat = data['lat']
    lng = data['lng']
    
    cursor.execute("INSERT INTO Favorites (channelId, title, location, lng, lat) VALUES (?, ?, ?, ?, ?)",
                   (channel_id, title, location, lng, lat))
    conn.commit()
    return {"message": "success"}

@app.get("/favorites")
async def get_favorites():
    cursor.execute("SELECT * from Favorites")
    rows = cursor.fetchall()
    return rows

@app.get("/favorite/{channelId}")
async def get_favorite(channelId: str):
    cursor.execute("SELECT * from Favorites where channelId=?", (channelId,))
    rows = cursor.fetchall()
    return rows

@app.delete("/favorite/{channelId}")
async def delete_favorite(channelId: str):
    cursor.execute("DELETE from Favorites where channelId=?", (channelId,))
    conn.commit()
    return {"message": "success"}

@app.get("/checkOnline")
async def check_online():
    url = "http://gstatic.com/generate_204"
    try:
        response = requests.get(url)
        if response.ok: return 204
        return 500
    except requests.exceptions.RequestException as e:
        print("Fetch Error")
        print(e)
        return 500

@app.post("/displayToggle")
async def display_toggle():
    #trigger.toggle()
    return {"message": "success", "displayState": 1}

@app.post("/displayOn")
async def display_on():
    #trigger.off()
    return {"message": "success", "displayState": 0}

@app.post("/displayOff")
async def display_off():
    #trigger.on()
    return {"message": "success", "displayState": 1}

@app.post("/restart")
async def restart():
    if platform.system() == "Linux":
        subprocess.run(["sudo", "reboot"])
    return {"message": "restarting"}

@app.post("/shutdown")
async def shutdown():
    if platform.system() == "Linux":
        subprocess.run(["sudo", "shutdown", "now"])
    return {"message": "shutting down"}

@app.get("/systemInfo")
async def system_info():
    net_info = {}
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            # Use socket module to get the address family
            addr_family = socket.AF_INET if addr.family == socket.AF_INET else socket.AF_INET6

            # Check if the address is IPv4
            if addr_family == socket.AF_INET:
                net_info[interface] = addr.address

    sys_info = {}
    sys_info["CPU Load"] = os.getloadavg()[0]

    # Check if the sensors_temperatures function returns the expected data structure
    temperatures = psutil.sensors_temperatures()
    if 'coretemp' in temperatures and len(temperatures['coretemp']) > 0:
        sys_info["CPU Temp"] = f"{temperatures['coretemp'][0].current} C"
    else:
        sys_info["CPU Temp"] = "N/A"

    return {"netInfo": net_info, "sysInfo": sys_info}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
