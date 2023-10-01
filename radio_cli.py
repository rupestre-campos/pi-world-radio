#!/usr/bin/python3
import requests
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import subprocess
import time
import json
import unicodedata


default_file_path = "./app/data/geo_json.min.json"
geojson_url = f"https://radio.garden/api/ara/content/places"


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode("utf-8")

def get_feature(d):
    feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [d['geo'][0], d['geo'][1]]}}
    feature['properties'] = {'title': remove_accents(d['title']), 'country': remove_accents(d['country']), 'location_id': d['id'], 'lng': d['geo'][0], 'lat': d['geo'][1]}
    return feature

def fetch_geojson_data(url, default_file_path):
    # todo add cache layer
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
    stations = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        city = feature['properties']['title']
        if country == selected_country and city == selected_city:
            station = feature['properties']['location_id']
            response = requests.get(f"https://radio.garden/api/ara/content/page/{station}/channels")
            data = response.json()
            return data["data"]["content"][0]["items"]

def play_stream(stream_url):
    print(" use  / * to decrease increase volume" )
    print(" use m to mute and q to quit" )
    try:
        # Use subprocess to execute the MPlayer command with the stream URL
        subprocess.run(['mpv',
                        '--cache-pause-initial=yes',
                        '--cache-pause=no',
                        #'--cache-default=15360',
                        #'--cache-initial=256',
                        '--demuxer-thread=yes',
                        '--demuxer-readahead-secs=30',
                        '--framedrop=vo',
                        '--sid=1',
                        '-cache-secs=30',
                        stream_url])
    except Exception as e:
        print(f"Error: {e}")

def main():

    geojson_data = fetch_geojson_data(geojson_url, default_file_path)

    if geojson_data:
        countries = list_countries(geojson_data)
        country_completer = WordCompleter(countries, ignore_case=True)
        selected_country = prompt('Select a country: ', completer=country_completer)

        cities = list_cities(geojson_data, selected_country)
        city_completer = WordCompleter(cities, ignore_case=True)
        selected_city = prompt('Select a city: ', completer=city_completer)

        stations = list_stations(geojson_data, selected_country, selected_city)
        station_completer = WordCompleter([station['title'] for station in stations], ignore_case=True)
        selected_station = prompt('Select a station: ', completer=station_completer)

        station_data = next((station for station in stations if station['title'] == selected_station), None)
        if station_data:
            channel_id = station_data["href"].split("/")[-1]
            val = int(time.time() * 1000)
            stream_url = f"https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{val}"
            print(f"Streaming URL: {stream_url}")
            play_stream(stream_url)
        else:
            print("Invalid station selection.")


if __name__ == "__main__":
    main()
