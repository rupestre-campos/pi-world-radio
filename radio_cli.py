#!/usr/bin/python3
import requests
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import subprocess
import time
import json
import unicodedata
import os

default_file_path = "/tmp/geo_json.min.json"
geojson_url = f"https://radio.garden/api/ara/content/places"

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
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad requests
        geo_json = {'type': 'FeatureCollection', 'features': []}
        rg_json = response.json()

        for item in rg_json['data']['list']:
            geo_json['features'].append(get_feature(item))
        with open(default_file_path, "w") as file_open:
            file_open.write(json.dumps(geo_json))
        return geo_json

    except requests.exceptions.RequestException as e:
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
            response = requests.get(f"https://radio.garden/api/ara/content/page/{station}/channels")
            data = response.json()
            for item in data["data"]["content"][0]["items"]:
                stations_dict[item["title"]] = item
    return stations_dict

def play_stream(stream_url):
    print("Hit  / to decrease and * to increase volume" )
    print("Hit space to pause, m to mute and q to quit" )
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

def main():
    clear()
    print("Welcome to radio.garden in a cli")
    geojson_data = fetch_geojson_data(geojson_url, default_file_path)

    if geojson_data:
        countries = list_countries(geojson_data)
        country_completer = WordCompleter(countries, ignore_case=True)
        print(" Hit Tab for a complete list or just start typing the names")
        selected_country = prompt('Select a country: ', completer=country_completer)
        if selected_country not in countries:
            print(" Country not in list, exiting...")
            return None
        cities = list_cities(geojson_data, selected_country)
        city_completer = WordCompleter(cities, ignore_case=True)
        selected_city = prompt('Select a city: ', completer=city_completer)
        if selected_city not in cities:
            print("City not in list, exiting...")
            return None

        stations_dict = list_stations(geojson_data, selected_country, selected_city)
        station_names = list(stations_dict.keys())
        station_completer = WordCompleter(station_names, ignore_case=True)

        while True:
            selected_station = prompt('Select a station: ', completer=station_completer)
            if selected_station not in station_names:
                print("Invalid station name. Please try again.")
                continue
            station_data = stations_dict[selected_station]
            channel_id = station_data["href"].split("/")[-1]
            val = int(time.time() * 1000)
            stream_url = f"https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{val}"
            print(f"Streaming {selected_station}")
            play_stream(stream_url)


if __name__ == "__main__":
    main()
