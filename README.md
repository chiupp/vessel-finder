# Real-time AIS and Radar Data Visualization

This project visualizes real-time AIS and radar data on a web-based map using Flask, Folium, and Bokeh.

## Project Overview

The project collects AIS and radar data, processes it, and visualizes it on a web-based map. The data is updated in real-time, and users can view information about various ships, including their positions, speed, and images.

## Features

- Real-time AIS data processing and visualization
- Real-time radar data processing and visualization
- Interactive map with ship positions and details
- WebSocket server for real-time data updates

##DEMO

https://github.com/chiupp/vessel-finder/assets/172878912/72c6b48e-d683-4346-82d9-57faa983c3a4

## Technologies Used

- Python
- Flask
- Folium
- Bokeh
- Selenium
- pyAIS
- WebSockets

## Project Structure
.
├── app.py
├── templates
│ └── index.html
├── static
│ └── custom.min.js
└── README.md

### `app.py`

Main application file that handles data collection, processing, and web server functionality.

### `templates/index.html`

HTML file for the web-based map interface.

### `static/custom.min.js`

JavaScript file for handling map interactions.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/real-time-ais-radar.git
    cd real-time-ais-radar
    ```

2. Set up a virtual environment and install dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Install ChromeDriver for Selenium (make sure it matches your Chrome version):
    - [Download ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

4. Ensure that you have Prometheus installed and running:
    - [Prometheus Installation Guide](https://prometheus.io/docs/prometheus/latest/installation/)

## Usage
1. Connect the AIS device, make sure the serial port 

2. Start the Flask web server:
    ```sh
    python app.py
    ```

3. Open  web browser and navigate to `http://localhost:5000` to view the real-time map.

## Acknowledgements

- [Folium](https://python-visualization.github.io/folium/)
- [Bokeh](https://bokeh.org/)
- [Selenium](https://www.selenium.dev/)
- [pyAIS](https://github.com/M0r13n/pyais)

