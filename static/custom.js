var map = L.map('map', {
    center: [39.73, -104.99],
    zoom: 10,
});

var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

var markers = L.layerGroup().addTo(map); // AIS標記的 Layer Group
var radarMarkers = L.layerGroup().addTo(map); // 雷達標記的 Layer Group

var baseMaps = {
    "OpenStreetMap": osm,
};

var overlayMaps = {
    "AIS Data": markers,
    "Radar Data": radarMarkers,
};

var layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map);


var socket = new WebSocket("ws://localhost:8765/");

socket.onmessage = function(event) {
    var data = JSON.parse(event.data);
    console.log('Received data:', data);

    if (data.radarDataList) {
        var radarDataList = data.radarDataList;
        updateRadarData(radarDataList); // 更新雷达数据的显示
    } else {
        updateMapMarkers(data); // 更新 AIS 数据的显示
    }
};

// 更新 AIS 数据的函数
function updateMapMarkers(markersData) {
    // 清空所有标记点
    aisMarkers.clearLayers();

    // 添加最新的位置点和图片到组合图层
    Object.entries(markersData).forEach(function([key, value]) {
        var lat = value[1];
        var lon = value[0];
        var time = value[2];
        var image_url = value[3];
        var ship_name = value[4];
        var ship_type = value[5];
        var sog = value[6];
        var cog = value[7];
        var mmsi = key;
        var marker = L.marker([lat, lon]);
        var popupContent = 'MMSI: ' + mmsi + '<br>Time: ' + time + '<br>Latitude: ' + lat + '<br>Longitude: ' + lon + '<br>SOG: ' + sog + '<br>COG: ' + cog;
        if (ship_name) {
            popupContent += '<br>Ship Name: ' + ship_name;
        }
        if (ship_type) {
            popupContent += '<br>Ship Type: ' + ship_type;
        }
        if (image_url) {
            popupContent += '<br><img src="' + image_url + '" width="120" height="100">';
        }
        marker.bindPopup(popupContent, { autoClose: false });

        // 添加到组合图层中
        aisMarkers.addLayer(marker); // 添加到 AIS 图层中
    });

    
}

// 更新雷达数据的函数
function updateRadarData(radarData) {
    // 清空所有雷达点
    radarMarkers.clearLayers();

    // 添加最新的雷达点到组合图层
    radarData.forEach(function(data) {
        var lat = data[1];
        var lon = data[0];
        var marker = L.marker([lat, lon]);
        var popupContent = 'Latitude: ' + lat + '<br>Longitude: ' + lon;
        marker.bindPopup(popupContent, { autoClose: false });

        // 添加到组合图层中
        radarMarkers.addLayer(marker); 
    });


}
