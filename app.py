import pyais
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import serial
from datetime import datetime
import folium
from bokeh.plotting import curdoc
from bokeh.models import Div, CustomJS
from bokeh.layouts import column
import websockets
import asyncio
from flask import Flask, render_template
from pyais import decode
from pyais.messages import MessageType1, MessageType2, MessageType3, MessageType4, MessageType18, MessageType19
import json
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from collections import OrderedDict
from waitress import serve
from prometheus_client import start_http_server, Counter
import socket


# Disable Chrome DevTools logs
chrome_options = Options()
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_argument('--headless=new')
driver = webdriver.Chrome(options=chrome_options)


m = folium.Map(location=[22.6, 120.3], zoom_start=14)

# Initialize the plotting object
div = Div(width=800, height=600)

# Dictionary to store the latest position points and image information for each MMSI
mmsi_dict = {}
radar_json_data = {}
# Open the serial port
ser = serial.Serial('COM3', 38400)

# radar
HOST = "192.168.199.140"
PORT = 10110
print((HOST, PORT))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

ship_info_cache = OrderedDict()
MAX_CACHE_SIZE = 15

MESSAGES_RECEIVED = Counter('messages_received_total', '接收到的訊息總數')
MESSAGES_PROCESSED_COUNTER = Counter('messages_processed_total', '處理的訊息總數')


def calculate_degrees_minutes_lat(extracted_data):
    degrees = int(extracted_data[:2])
    minutes = float(extracted_data[2:])
    return degrees + minutes / 60

def calculate_degrees_minutes_lon(extracted_data):
    degrees = int(extracted_data[:3])
    minutes = float(extracted_data[3:])
    return degrees + minutes / 60

def get_ship_info(mmsi):
    if mmsi in ship_info_cache:
        # Move the accessed entry to the end to maintain LRU order
        ship_info = ship_info_cache.pop(mmsi)
        ship_info_cache[mmsi] = ship_info
        return ship_info

    search_url = 'https://www.vesselfinder.com/gallery'
    driver.get(search_url)

    if mmsi:
        search_input = driver.find_element(By.ID, 's2')
        search_input.send_keys(mmsi)
        try:
            WebDriverWait(driver, 2.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ts-results li.ts-item')))
            first_result = driver.find_element(By.CSS_SELECTOR, 'ul.ts-results li.ts-item')
            ship_name = first_result.find_element(By.CSS_SELECTOR, 'div.name').text.strip()
            ship_type = first_result.find_element(By.CSS_SELECTOR, 'div.styp').text.strip()
            first_result.click()
        except (NoSuchElementException, TimeoutException):
            ship_name = None
            ship_type = None
    else:
        return None

    try:
        WebDriverWait(driver, 2.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.picture.jg-entry.entry-visible img')))
        image_element = driver.find_element(By.CSS_SELECTOR, 'div.picture.jg-entry.entry-visible img')
        image_url = image_element.get_attribute('src')
    except TimeoutException:
        image_url = None
    ship_info_cache[mmsi] = (ship_name, ship_type, image_url)
    if len(ship_info_cache) > MAX_CACHE_SIZE:
        ship_info_cache.popitem(last=False)
    return ship_name, ship_type, image_url


def update_data():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def connect_to_websocket():
        while True:
            try:
                async with websockets.connect('ws://localhost:8765/', ping_timeout=10) as websocket:
                    while True:

                        line = ser.readline().strip()
                        if line.startswith(b'!AIVDM') or line.startswith(b'!AIVDO'):
                            try:

                                msg = decode(line)
                                if isinstance(msg, (
                                        MessageType1, MessageType2, MessageType3, MessageType18,
                                        MessageType19)):
                                    lon = msg.lon
                                    lat = msg.lat
                                    mmsi = msg.mmsi
                                    sog = msg.speed
                                    cog = msg.course

                                    # Skip if mmsi is 0
                                    if mmsi == 0:
                                        continue

                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    print(f'Time: {timestamp}, MMSI: {mmsi}, 經度: {lon}, 緯度: {lat}')
                                    MESSAGES_RECEIVED.inc()
                                    # Get the image URL
                                    ship_name, ship_type, image_url = get_ship_info(mmsi)

                                    mmsi_dict[mmsi] = (lon, lat, timestamp, image_url, ship_name, ship_type, sog, cog)

                                    # Generate JavaScript code to add the latest position point to the map
                                    js_code = "updateMapMarkers({});".format(json.dumps(mmsi_dict))

                                    # Use CustomJS to execute the JavaScript code in the frontend
                                    curdoc().add_next_tick_callback(CustomJS(code=js_code))

                                    # Update the map and graph
                                    div.text = f'MMSI: {mmsi}<br>Time: {timestamp}<br>Latitude: {lat}<br>Longitude: {lon}<br>SOG: {sog}<br>COG: {cog}'
                                    if ship_name:
                                        div.text += f'<br>Ship Name: {ship_name}'
                                    if ship_type:
                                        div.text += f'<br>Ship Type: {ship_type}'
                                    if image_url:
                                        div.text += f'<br><img src="{image_url}" width="120" height="100">'
                                    curdoc().add_root(column(div))



                            except pyais.exceptions.MissingMultipartMessageException:
                                print(f"Missing fragment numbers in AIS message: {line}")
                                continue
                            except pyais.exceptions.InvalidNMEAMessageException:
                                print(f"Invalid NMEA sentence: {line}")
                                continue

            except websockets.exceptions.ConnectionClosedError:
                print("WebSocket connection closed. Reconnecting...")
                await asyncio.sleep(4)  # Wait for some time before attempting to reconnect

    loop.run_until_complete(connect_to_websocket())

def update_radar():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def connect_to_radar():
        global radar_json_data
        while True:
            try:
                data = s.recv(1024)
                lines = data.splitlines()

                if not data:
                    break
                extracted_data = [line.decode() for line in lines if line.startswith(b"$GPGLL")]
                radar_data_list = []
                for data in extracted_data:
                    data_parts = data.strip().split(",")
                    if len(data_parts) >= 6:
                        latitude = calculate_degrees_minutes_lat(data_parts[1])
                        longitude = calculate_degrees_minutes_lon(data_parts[3])
                        radar_data_list.append((longitude, latitude))
                print("Radar data extracted:", radar_data_list)
                if radar_data_list:
                # Convert radar_data_list to JSON format
                    radar_json_data = json.dumps({
                        'radarDataList': radar_data_list
                    })
                # Generate JavaScript code to update radar data on the frontend
                    js_code = "updateRadarData({});".format(radar_json_data)
                    # Use CustomJS to execute the JavaScript code in the frontend
                    curdoc().add_next_tick_callback(CustomJS(code=js_code))
                    print(radar_json_data)
                    await asyncio.sleep(6)
                else:
                    print("No radar data to send to frontend")
                    await asyncio.sleep(6)
            except socket.error as e:
                print(f"Socket 錯誤: {e}")
                break

    loop.run_until_complete(connect_to_radar())

def start_websocket_server():
    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def websocket_handler(websocket, path):
                while True:
                    try:
                        await websocket.send(json.dumps(mmsi_dict))

                        await asyncio.sleep(3)
                        await websocket.send(json.dumps({"radarDataList": radar_json_data}))
                        print("Radar data sent:", json.dumps({"radarDataList": radar_json_data}))
                    except websockets.exceptions.ConnectionClosedError:
                        print("WebSocket connection closed. Reconnecting...")
                        break

            MESSAGES_PROCESSED_COUNTER.inc()
            start_server = websockets.serve(websocket_handler, 'localhost', 8765)
            loop.run_until_complete(start_server)
            loop.run_forever()

        except Exception as e:
            print(f"WebSocket server error: {str(e)}")
            print("Retrying in 4 seconds...")
            time.sleep(4)



# Create the Flask application
app = Flask(__name__)


# Route settings
@app.route('/')
def index():
    return render_template('index.html')


# Convert the map to HTML code
map_html = m._repr_html_()

# Update the map and graph
div.text = map_html
curdoc().add_root(column(div))

# Main program
if __name__ == '__main__':
    # Start the WebSocket server thread
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.start()

    # Start the data update thread
    update_thread = threading.Thread(target=update_data)
    update_thread.start()

    radar_thread = threading.Thread(target=update_radar)
    radar_thread.start()

    start_http_server(8000)
    # Start the Flask application
    serve(app, host='0.0.0.0', port=5000)
