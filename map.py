import sqlite3

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.window import Window
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy_garden.mapview import MapMarkerPopup, MapMarker, MapView, MarkerMapLayer
from kivy.clock import Clock
from pywaterml import waterML
from datetime import datetime
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg # type: ignore

class MapScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.station_id = None

    def get_lat_lon(self):
        latitudes = []
        longitudes = []
        
        # Connect to the database and retrieve latitudes and longitudes
        conn = sqlite3.connect("originalsample.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM StreamMidpoints")
        records = cursor.fetchall()

        for record in records:
            latitudes.append(record[1])
            longitudes.append(record[2])

        conn.close()

        return latitudes, longitudes
    
    def get_station_id(self, lat, lon):
        # conn = sqlite3.connect("datasample.db")
        conn = sqlite3.connect("originalsample.db")
        cursor = conn.cursor()
        cursor.execute("SELECT station_id FROM StreamMidpoints WHERE lat = ? AND lon = ?", (lat, lon))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]  # Return the station_id value
        else:
            return None  # Return None if no matching record found
        
    def on_marker_press(self, marker):
        lat = float(marker.lat)
        lon = float(marker.lon)
        station_id = self.get_station_id(lat, lon)
        if station_id:
            print(f"Station ID for marker at ({lat}, {lon}): {station_id}")
            self.ids.station_id.text = f"{station_id}"
        else:
            print(f"No station ID found for the marker at ({lat}, {lon}).")
        return station_id

    def create_markers(self):

        # Get the bounding box coordinates
        bbox = self.ids.main_map.get_bbox()
        min_lat, min_lon, max_lat, max_lon = bbox

        # Retrieve latitudes and longitudes
        latitudes, longitudes = self.get_lat_lon()

        # print(f'lat: {latitudes}, lon: {longitudes}')
        print(f"This is the bounding box: {bbox}")

        # Calculate marker size based on the zoom level
        zoom = self.ids.main_map.zoom
        marker_size = 500 / zoom

        # Iterate over the children of the MapView widget to find the MarkerMapLayer
        for child in self.ids.main_map.children:
            if isinstance(child, MarkerMapLayer):
                marker_map_layer = child
                break
        else:
            # If MarkerMapLayer is not found, create a new one and add it to the MapView
            marker_map_layer = MarkerMapLayer()
            self.ids.main_map.add_layer(marker_map_layer)

        # Iterate over the latitudes and longitudes and add markers inside the bounding box
        for lat, lon in zip(latitudes, longitudes):
            if min_lat-.5 <= lat <= max_lat+.5 and min_lon-.5 <= lon <= max_lon+.5:
                new_marker = MapMarker(lat=str(lat), lon=str(lon), source = "icon2.png")
                new_marker.size = [marker_size for size in new_marker.texture_size]
                new_marker.bind(on_press=self.on_marker_press)
                marker_map_layer.add_widget(new_marker)

class ForecastScreen(MDScreen):
    def display_plot(self, datetimes, values):
        # Create a new figure
        plt.figure(figsize=(7, 6))
        plt.plot(datetimes, values, marker='o')
        plt.title('Carson Beach Air Temp')
        plt.xlabel('Date')
        plt.ylabel('Temp (Celcius Degrees)')
        plt.grid(True)
        plt.tight_layout()
        
        # Convert the plot to a Kivy-compatible texture
        canvas = FigureCanvasKivyAgg(plt.gcf())
        self.ids.plot_container.add_widget(canvas)

    def get_data_from_hydroserver(self):
        # Connect to the Massachusetts Water Resources Authority (MWRA) HydroServer service
        url = "https://hydroportal.cuahsi.org/MWRA/cuahsi_1_1.asmx?WSDL"
        site_full_code = "MWRA:36"  # Notice that "full code"
        variable_full_code = "MWRA:Temp"  # Notice that "full code"
        start_date = "2005-12-04"
        end_date = "2006-07-06"

        # Get the WaterMLOperations object
        water = waterML.WaterMLOperations(url)
        sites = water.GetSites()
        data = water.GetValues(site_full_code, variable_full_code, start_date, end_date)["values"]

        # Extract datetimes and values from the data object
        datetimes = [datetime.strptime(d['dateTime'], '%Y-%m-%d %H:%M:%S') for d in data]
        values = [d['dataValue'] for d in data]

        return datetimes, values

    def on_pre_enter(self, *args):
        # Get data from the HydroServer
        datetimes, values = self.get_data_from_hydroserver()
        
        # Display the plot in the ForecastScreen
        self.display_plot(datetimes, values)

class ScreenManager(MDScreenManager):
  pass

# Set the app size
Window.size = (350, 600)

class nwmApp(MDApp):
  def build(self):
    self.theme_cls.theme_style = "Light"
    self.theme_cls.primary_palette = "Peru"

    # Create a ScreenManager and add screens
    screen_manager = ScreenManager()
    map_screen = MapScreen(name="map")
    forecast_screen = ForecastScreen(name="forecast")
    screen_manager.add_widget(map_screen)
    screen_manager.add_widget(forecast_screen)
    
    # Schedule the creation of markers after a short delay
    Clock.schedule_once(lambda dt: map_screen.create_markers(), .1)

    return screen_manager


if __name__ == '__main__':
  nwmApp().run()