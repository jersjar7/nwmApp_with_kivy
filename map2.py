import sqlite3

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.window import Window
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy_garden.mapview import MapMarkerPopup, MapMarker, MapView, MarkerMapLayer
from kivy.clock import Clock
from KivyMD.kivymd.uix.boxlayout import MDBoxLayout

class MapScreen(MDScreen):
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
        marker_size = 700 / zoom

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

        # Add new markers using the latitudes and longitudes
        # for lat, lon in zip(latitudes, longitudes):
        #     new_marker = MapMarker(lat=str(lat), lon=str(lon))
        #     marker_map_layer.add_widget(new_marker)

        # Print the coordinates of the newly added markers
        # for marker in marker_map_layer.children:
        #     if isinstance(marker, MapMarker):
        #         print(f'New MapMarker: lat={marker.lat}, lon={marker.lon}')

                
# This is part of me finding out how the mapview is structured
        # Iterate over the children of the MapView widget
#         for child in self.ids.main_map.children:
#             if isinstance(child, MarkerMapLayer):
#                 # Iterate over the children of MarkerMapLayer
#                 for marker in child.children:
#                     if isinstance(marker, MapMarker):
#                         print(f'MapMarker: lat={marker.lat}, lon={marker.lon}')

#         # Create and add new markers based on the lists of latitudes and longitudes
#         for lat, lon in zip(latitudes, longitudes):
#             new_marker = MapMarker(lat=str(lat), lon=str(lon))
#             self.ids.main_map.add_widget(new_marker)
    
# # This was great to help find the children of MapView in the kv. file
# # Turns out it has 3 children and MapMarker is an object inside one of
# # the children MarkerMapLayer

#         # Iterate over the keys in the ids dictionary:
#         for key in self.ids.keys():
#             print(key)
        
#         # Iterate over the children of the MapView widget
#         for child in self.ids.main_map.children:
#             # Check if the child is a MapMarker
#             if isinstance(child, MapMarker):
#                 # Access the lat and lon attributes of the MapMarker
#                 print(f'Lat: {child.lat}, Lon: {child.lon}')
        
        

class ForecastScreen(MDScreen):
  pass

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
    Clock.schedule_once(lambda dt: map_screen.create_markers(), 0.0001)

    return screen_manager


if __name__ == '__main__':
  nwmApp().run()