#!/usr/bin/python3
# coding: utf-8
import os
import time
import json
import random
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import subprocess
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from unidecode import unidecode
from inputimeout import inputimeout, TimeoutOccurred
try:
    import fiona
    import gj2ascii
    libs_plot_map = True
except Exception as e:
    libs_plot_map = False

is_history_favorites_enabled = True

geojson_url = "https://radio.garden/api/ara/content/places"
stations_url_pattern = "https://radio.garden/api/ara/content/page/{station_id}/channels"
stream_url_pattern = "https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{time_value}"

HOME_DIR = os.path.expanduser("~")
DEFAULT_DIR = os.path.join(HOME_DIR, ".piradio")

DEFAULT_DATA_FILE_PATH = os.path.join(DEFAULT_DIR,"radios.geojson")
DEFAULT_HISTORY_FILE_PATH = os.path.join(DEFAULT_DIR, "history.json")
DEFAULT_FAVORITES_FILE_PATH = os.path.join(DEFAULT_DIR, "favorites.json")
LOCATION_DATA_FILE = os.path.join(DEFAULT_DIR, "location_data.geojson")

TIMEOUT_CON = 10
TIMEOUT_FETCH = 10
TIMEOUT_STREAM = 5
TIME_RETRY_STREAM = 3
MAP_WIDTH = 110

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

def make_default_dir():
    try:
        if os.path.isdir(DEFAULT_DIR): return 1
        os.mkdir(DEFAULT_DIR)
        return 1
    except Exception as e:
        return 0

def clear():
    try:
        subprocess.run(["cls"] if os.name == "nt" else ["clear"])
        return 1
    except Exception as e:
        return 0

def get_feature(d):
    feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [d['geo'][0], d['geo'][1]]}}
    feature['properties'] = {
        'title': unidecode(d['title']),
        'country': unidecode(d['country']),
        'location_id': d['id'],
        'lng': d['geo'][0], 'lat': d['geo'][1]
    }
    return feature

def get_geojson_new():
    return {'type': 'FeatureCollection', 'features': []}


def fetch_geojson_data(url, default_file_path):
    try:
        response = session.get(url, timeout=(TIMEOUT_CON, TIMEOUT_FETCH))
        response.raise_for_status()  # Raise exception for bad requests
        geo_json = get_geojson_new()
        rg_json = response.json()

        for item in rg_json['data']['list']:
            geo_json['features'].append(get_feature(item))
        with open(default_file_path, "w") as file_open:
            file_open.write(json.dumps(geo_json))
        return geo_json

    except Exception as e:
        print("Error fetching GeoJSON data")
        return {}

def list_countries(geojson_data):
    countries = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country not in countries:
            countries.append(unidecode(country))
    return sorted(countries)

def list_cities(geojson_data, selected_country):
    cities = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country == selected_country:
            city = feature['properties']['title']
            cities.append(city)
    return sorted(cities)

def get_city_info(geojson_data, country, city):
    for feature in geojson_data['features']:
        if feature['properties']['country'] == country and \
           feature['properties']['title'] == city:
            return feature

def list_stations(geojson_data, selected_country, selected_city):
    stations_dict = {}
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        city = feature['properties']['title']
        if country == selected_country and city == selected_city:
            station = feature['properties']['location_id']
            response = session.get(
                stations_url_pattern.format(station_id=station),
                timeout=(TIMEOUT_CON,TIMEOUT_FETCH))
            data = response.json()
            for item in data["data"]["content"][0]["items"]:
                stations_dict[unidecode(item["page"]["title"])] = item["page"]
    return stations_dict

def play_stream(stream_url):
    print("Player Control")
    print("/ decrease volume\n* increase volume")
    print("space pause\nm mute\nq exit to main menu")

    subprocess.run([
        'mpv',
        '--no-video',
        f'--network-timeout={TIMEOUT_STREAM}',
        '--stream-lavf-o=reconnect_streamed=1',
        '--cache=no',
        '--demuxer-thread=yes',
        '--framedrop=vo',
        '--sid=1',
        stream_url])

def create_user_selection_map():
    return {
         "country": "",
         "city": "",
         "station": ""
    }

def read_stations(default_file_path):
    data = {}
    if not os.path.exists(default_file_path):
        return data
    with open(default_file_path, "r") as file_open:
        for line_str in file_open:
            line = json.loads(line_str)
            if not line["country"] in data:
                data[line["country"]] = {}
            if not line["location"] in data[line["country"]]:
                data[line["country"]][line["location"]] = []
            data[line["country"]][line["location"]].append(line["station"])
    return data

def write_stations(default_file_path, selected_country, selected_city, selected_station):
    with open(default_file_path, "a") as file_open:
        file_open.write(json.dumps({
            "country": selected_country,
            "location": selected_city,
            "station": selected_station
        }, ensure_ascii=False))
        file_open.write("\n")

def main():
    world_map = get_countries_ascii()
    clear()
    make_default_dir()
    geojson_data = fetch_geojson_data(geojson_url, DEFAULT_DATA_FILE_PATH)

    if not geojson_data:
        print("Couldn't get data from internet")
        return None
    user_selection = create_user_selection_map()

    run_until_complete = True
    while run_until_complete:
        try:
            #clear()
            print("Welcome to radio.garden in a cli")
            print("Instructions:")
            print("Start by chosing between historic (h) favorites (f) or to start fresh new search (anything)")
            print("Then Search countries, locations and stations as prompted, start to type to filter")
            print("tab for a complete list\nenter for last used or random one if none\nr or nothing to shuffle")
            print("q to restart\nctrl + c to exit")
            print("#"*25+"\n")
            countries = list_countries(geojson_data)


            if is_history_favorites_enabled:
                user_browse_history = False
                user_browse_favorites = False

                history = read_stations(DEFAULT_HISTORY_FILE_PATH)
                favorites = read_stations(DEFAULT_FAVORITES_FILE_PATH)

                browse_history_favorites = input("Browse history(h) or favorites(f)? Enter anything else to start new\n[h/f]")
                browse_history_favorites = browse_history_favorites.strip().lower()

                if browse_history_favorites in ["h","f"]:
                    if browse_history_favorites == "h":
                        user_browse_history = True
                        countries = sorted(history.keys())

                    else:
                        user_browse_favorites = True
                        countries = sorted(favorites.keys())

            country_completer = FuzzyWordCompleter(countries)
            selected_country = prompt("Select a country:", completer=country_completer)

            if selected_country == "q":
                continue
            if selected_country == "" and user_selection["country"]!="":
                selected_country = user_selection["country"]
            if (selected_country == "" and user_selection["country"]=="")\
               or selected_country.strip().lower() == "r" :
                selected_country = random.choices(countries)[0]
            if selected_country not in countries:
                print(" Country not in list, try again...")
                print("#"*25)
                continue
            user_selection["country"] = selected_country
            print(selected_country)

            if user_browse_history:
                cities = sorted(history[selected_country].keys())
            elif user_browse_favorites:
                cities = sorted(favorites[selected_country].keys())
            else:
                cities = list_cities(geojson_data, selected_country)

            city_completer = FuzzyWordCompleter(cities)
            selected_city = prompt('Select a location: ', completer=city_completer)

            user_selection_city_in_list = user_selection["city"] in cities
            if selected_city == "q":
                continue
            if selected_city == "" and user_selection_city_in_list:
                selected_city = user_selection["city"]
            if (selected_city == "" and not user_selection_city_in_list)\
                or selected_city.strip().lower() == "r":
                selected_city = random.choices(cities)[0]
            if selected_city not in cities:
                print("Location not in list, try again...")
                print("#"*25)
                continue
            user_selection["city"] = selected_city
            print(selected_city)
            stacked = world_map
            if libs_plot_map:
                city_info = get_city_info(geojson_data, selected_country, selected_city)
                new_json = get_geojson_new()
                new_json["features"].append(city_info)
                with open(LOCATION_DATA_FILE, "w") as f:
                    f.write(json.dumps(new_json, indent=4))

                with fiona.open(LOCATION_DATA_FILE, "r") as radio_geo:
                    map_plot = []
                    map_plot.append(world_map)
                    map_plot.append(gj2ascii.render(
                        radio_geo, MAP_WIDTH, char="A", fill=" ",bbox=(-180,-90,180,90), all_touched=True))
                stacked = gj2ascii.stack(map_plot, fill=" ")

            stations_dict = list_stations(geojson_data, selected_country, selected_city)
            if user_browse_history:
                station_names = sorted(history[selected_country][selected_city])
            elif user_browse_favorites:
                station_names = sorted(favorites[selected_country][selected_city])
            else:
                station_names = sorted(list(stations_dict.keys()))

            station_completer = FuzzyWordCompleter(station_names)
            selected_station = prompt("Select a station:", completer=station_completer)

            user_selection_station_in_list = user_selection["station"] in stations_dict
            if selected_station == "q":
                continue
            if selected_station == "" and user_selection_station_in_list:
                selected_station = user_selection["station"]
            if (selected_station == "" and not user_selection_station_in_list)\
                or selected_station.lower() == "r":
                selected_station = random.choices(station_names)[0]
            if selected_station not in stations_dict:
                print(" Station not in list, try again...")
                continue
            user_selection["station"] = selected_station
            print(selected_station)

            station_data = stations_dict[selected_station]
            channel_id = station_data["url"].split("/")[-1]
            #clear()
            playing = True
            if is_history_favorites_enabled \
               and not selected_station in history.get(selected_country,{}).get(selected_city,{}):
                write_stations(DEFAULT_HISTORY_FILE_PATH,selected_country, selected_city, selected_station)

            while playing:
                print(f"Country: {selected_country}")
                print(f"Location: {selected_city}")
                print(f"Station: {selected_station}")

                print(stacked)

                time_value = int(time.time() * 1000)
                stream_url = stream_url_pattern.format(channel_id=channel_id, time_value=time_value)
                try:
                    play_stream(stream_url)
                    user_input = inputimeout(prompt="Really quit? press q + enter", timeout=TIME_RETRY_STREAM)
                    if user_input.strip().lower() == "q":
                        playing = False
                except KeyboardInterrupt:
                    playing = False
                except TimeoutOccurred:
                    continue
                except Exception as e:
                    print(f"error: {e}")
                    playing = False
            #clear()
            if is_history_favorites_enabled \
               and not selected_station in favorites.get(selected_country,{}).get(selected_city,{}):
                print("#"*25+"\n")
                add_to_favorites = input(f"Add to favorites?\n{selected_country}\n{selected_city}\n{selected_station}\n[y/n]")
                if add_to_favorites.strip().lower() == "y":
                    write_stations(DEFAULT_FAVORITES_FILE_PATH,selected_country, selected_city, selected_station)

        except KeyboardInterrupt as e:
            clear()
            print("Exiting")
            return None

        except Exception as e:
            #clear()
            print(f"Error {e}")
            return None

def get_countries_ascii():
    return """                                                                                                             
                          . . .   . . . . . . .             . . .                                            
                  .     . . . .       . . . . .                                 . . . . .   .                
.     . . . . . . . . . . . .   . .   . . .                 . .   .   . . . . . . . . . . . . . . . . . . . .
    . . . . . . . . . . .       .                       . .   . . . . . . . . . . . . . . . . . . . .   . .  
                . . . . . . . . . .                 .     . . . . . . . . . . . . . . . . . . . .     .      
                  . . . . . . . . .                   . . . . . . . . . . . . . . . . . . . . . .            
                  . . . . . . .                     . .     . . . . .   . . . . . . . . . . .                
                  . . . . . . .                     . . .         . . . . . . . . . . . . .                  
                      . .                           . . . . . . . . . . . . . . . . . . . .                  
                      . .                         . . . . . . . . . . . .   . . .   . .                      
                          . .                     . . . . . . . . . .         .     . .                      
                                . .                 . . . . . . . . .                       .                
                              . . . . .                   . . . . .                     . .                  
                              . . . . . . .               . . . .                     .         . .          
                                . . . . . .                 . . . .                           .              
                                  . . . .                 . . . .   .                       . . . .          
                                  . . .                     . . .   .                     . . . . . .        
                                  . . .                     . .                           . . . . . .        
                                . . .                                                             .          
                                . .                                                                       .  
                                .                                                                            
                                                                                                             
                                    .                                                                        
                                  .                       .   . . . . . . .   . . . . . . . . . . . . .      
          . . . . . . . . . . .               . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      
    . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    """

if __name__ == "__main__":
    main()
