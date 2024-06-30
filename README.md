# Real-time AIS and Radar Data Visualization

This project visualizes real-time AIS data on a web-based map using Flask, Folium, and Bokeh.

## Project Overview

The project collects AIS and radar data, processes it, and visualizes it on a web-based map. The data is updated in real-time, and users can view information about various ships, including their positions, speed, and images.

## Features

- Real-time AIS data processing and visualization
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

```plaintext
├── app.py                 # Main application file
├── templates
│   └── index.html         # HTML file for the web-based map interface
├── static
│   └── custom.min.js      # JavaScript file for handling map interactions
└── README.md              # Project documentation
```

## Acknowledgements

- [Folium](https://python-visualization.github.io/folium/)
- [Bokeh](https://bokeh.org/)
- [Selenium](https://www.selenium.dev/)
- [pyAIS](https://github.com/M0r13n/pyais)

