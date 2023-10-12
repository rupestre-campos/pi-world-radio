#!/usr/bin/python3
import requests
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import subprocess
import time
import json
import unicodedata
import os
import random

default_file_path = "/tmp/geo_json.min.json"
geojson_url = f"https://radio.garden/api/ara/content/places"
TIMEOUT_CON = 10
TIMEOUT_FETCH = 10

def clear():
    try:
        subprocess.run(["clear"])
    except:
        pass

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode("utf-8")

def get_feature(d):
    feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [d['geo'][0], d['geo'][1]]}}
    feature['properties'] = {'title': remove_accents(d['title']), 'country': remove_accents(d['country']), 'location_id': d['id'], 'lng': d['geo'][0], 'lat': d['geo'][1]}
    return feature

def fetch_geojson_data(url, default_file_path):
    try:
        response = requests.get(url, timeout=(TIMEOUT_CON, TIMEOUT_FETCH))
        response.raise_for_status()  # Raise exception for bad requests
        geo_json = {'type': 'FeatureCollection', 'features': []}
        rg_json = response.json()

        for item in rg_json['data']['list']:
            geo_json['features'].append(get_feature(item))
        with open(default_file_path, "w") as file_open:
            file_open.write(json.dumps(geo_json))
        return geo_json

    except requests.exceptions.RequestException as e:
        print(e)
        #import pdb; pdb.set_trace()
        if os.path.exists(default_file_path):
            with open(default_file_path) as file_open:
                geo_json = json.load(file_open)
                return geo_json

        print("Error fetching GeoJSON data:", e)
        return None

def list_countries(geojson_data):
    countries = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country not in countries:
            countries.append(country)
    return sorted(countries)

def list_cities(geojson_data, selected_country):
    cities = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country == selected_country:
            city = feature['properties']['title']
            cities.append(city)
    return sorted(cities)

def list_stations(geojson_data, selected_country, selected_city):
    stations_dict = {}
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        city = feature['properties']['title']
        if country == selected_country and city == selected_city:
            station = feature['properties']['location_id']
            response = requests.get(f"https://radio.garden/api/ara/content/page/{station}/channels", timeout=(10,10))
            data = response.json()
            for item in data["data"]["content"][0]["items"]:
                stations_dict[remove_accents(item["page"]["title"])] = item["page"]
    return stations_dict

def play_stream(stream_url):
    print("Player Control")
    print(" / decrease volume\n * increase volume" )
    print(" space to pause\n m to mute\n q to quit" )
    try:
        # Use subprocess to execute the MPlayer command with the stream URL
        subprocess.run(['mpv',
                        '--cache-pause-initial=yes',
                        '--cache-pause=no',
                        '--demuxer-thread=yes',
                        '--demuxer-readahead-secs=30',
                        '--framedrop=vo',
                        '--sid=1',
                        '-cache-secs=30',
                        stream_url])
    except Exception as e:
        print(f"Error: {e}")

def create_user_selection_map():
    return {
         "country": "",
         "city": "",
         "station": ""
    }

def main():
    clear()
    print("Welcome to radio.garden in a cli")
    geojson_data = fetch_geojson_data(geojson_url, default_file_path)

    if not geojson_data:
        print("Couldn't get data from internet")
        return None
    user_selection = create_user_selection_map()
    countries = list_countries(geojson_data)
    country_completer = WordCompleter(countries, ignore_case=True)

    run_until_complete = True
    while run_until_complete:
        try:
            print("Instructions:\n Search as you type")
            print(" tab for a complete list\n enter for last used or random one if none\n send r to shuffle again")
            print(" ctrl + c to exit")
            print("#"*25)
            selected_country = prompt("Select a country:", completer=country_completer)

            if selected_country == "" and user_selection["country"]!="":
                selected_country = user_selection["country"]
            if (selected_country == "" and user_selection["country"]=="")\
               or selected_country.lower() == "r" :
                selected_country = random.choices(countries)[0]
            if selected_country not in countries:
                print(" Country not in list, try again...")
                print("#"*25)
                continue
            user_selection["country"] = selected_country
            print(selected_country)

            cities = list_cities(geojson_data, selected_country)
            city_completer = WordCompleter(cities, ignore_case=True)
            selected_city = prompt('Select a location: ', completer=city_completer)
            user_selection_city_in_list = user_selection["city"] in cities
            if selected_city == "" and user_selection_city_in_list:
                selected_city = user_selection["city"]
            if (selected_city == "" and not user_selection_city_in_list)\
                or selected_city.lower() == "r":
                selected_city = random.choices(cities)[0]
            if selected_city not in cities:
                print("Location not in list, try again...")
                print("#"*25)
                continue
            user_selection["city"] = selected_city
            print(selected_city)

            stations_dict = list_stations(geojson_data, selected_country, selected_city)
            station_names = sorted(list(stations_dict.keys()))
            station_completer = WordCompleter(station_names, ignore_case=True)
            selected_station = prompt("Select a station:", completer=station_completer)
            user_selection_station_in_list = user_selection["station"] in stations_dict
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
            val = int(time.time() * 1000)
            stream_url = f"https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{val}"
            clear()
            print(f"Country: {selected_country}")
            print(f"Location: {selected_city}")
            print(f"Station: {selected_station}")
            play_stream(stream_url)
            clear()

        except KeyboardInterrupt as e:
            clear()
            print("Exiting")
            return None

        except Exception as e:
            clear()
            print(f"Error {e}")
            return None

if __name__ == "__main__":
    main()
