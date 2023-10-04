#!/usr/bin/python3
import os
import json
import time
import sys
import urwid
import requests
import unicodedata
import subprocess
from collections import defaultdict
from requests.adapters import HTTPAdapter, Retry

session = requests.Session()
retries = Retry(total=2, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

READ_TIMEOUT = 1
CONN_TIMEOUT = 2
TIMEOUT = (CONN_TIMEOUT, READ_TIMEOUT)

default_file_path = "/tmp/geo_json.min.json"
geojson_url = f"https://radio.garden/api/ara/content/places"

palette = [
    (None,  'light gray', 'black'),
    ('heading', 'black', 'light gray'),
    ('line', 'black', 'light gray'),
    ('options', 'dark gray', 'black'),
    ('focus heading', 'white', 'dark red'),
    ('focus line', 'black', 'dark red'),
    ('focus options', 'black', 'light gray'),
    ('selected', 'white', 'dark blue')]

focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line'}

COLUMN_SIZE = 29
ROW_SIZE = 100

class HorizontalBoxes(urwid.Columns):
    def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

    def open_box(self, box):
        if self.contents:
            del self.contents[self.focus_position + 1:]
        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
            self.options('given' , COLUMN_SIZE)))
        self.focus_position = len(self.contents) - 1


class MenuButton(urwid.Button):
    def __init__(self, caption, callback):
        super(MenuButton, self).__init__("")
        urwid.connect_signal(self, 'click', callback)
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', caption], 2), None, 'selected')


class SubMenu(urwid.WidgetWrap):
    def __init__(self, caption, choices):
        super(SubMenu, self).__init__(MenuButton(
            [caption, u"\N{HORIZONTAL ELLIPSIS}"], self.open_menu))
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text([u"\n  ", caption]), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()] + choices + [urwid.Divider()]))
        self.menu = urwid.AttrMap(listbox, 'options')

    def open_menu(self, button):
        top.open_box(self.menu)


class Country(urwid.WidgetWrap):
    def __init__(self, caption, locations):
        super(Country, self).__init__(MenuButton(
            [caption, u"\N{HORIZONTAL ELLIPSIS}"], self.list_locations))
        self.caption = caption
        self.locations = locations

    def get_locations(self):
        locations = []
        for location, item in sorted(self.locations.items()):
            locations.append(
                Location(
                    location,
                    item.get("id"),
                    item.get("geometry"),
                    self.caption))
        return locations

    def list_locations(self, button):
        response = urwid.Text([u'  Locations in ', self.caption, u'\n'])
        locations = self.get_locations()
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text([u"\n  ", self.caption]), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()] + locations + [urwid.Divider()]))
        self.menu = urwid.AttrMap(listbox, 'options')
        top.open_box(self.menu)


class Location(urwid.WidgetWrap):
    def __init__(self, caption, location_id, geom, country):
        super(Location, self).__init__(
            MenuButton(caption, self.list_radios))
        self.caption = caption
        self.location_id = location_id
        self.geom = geom
        self.country = country

    def get_stations(self):
        try:
            response = session.get(
                f"https://radio.garden/api/ara/content/page/{self.location_id}/channels",
                timeout=TIMEOUT
            )
        except Exception as e:
            return []
        if not response.ok: return []
        data = response.json()
        stations = []
        for item in sorted(data["data"]["content"][0]["items"], key=lambda item: item.get("title")):
            item.update({"country": self.country, "location": self.caption, "geom": self.geom})
            stations.append(Station(item["title"], item))
        return stations

    def list_radios(self, button):
        response = urwid.Text([u'  You chose ', self.caption, u'\n'])
        stations = self.get_stations()
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text([u"\n  ", self.caption]), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()] + stations + [urwid.Divider()]))
        self.menu = urwid.AttrMap(listbox, 'options')
        top.open_box(self.menu)


class Station(urwid.WidgetWrap):
    def __init__(self, caption, item):
        super(Station, self).__init__(
            MenuButton(caption, self.play_radio))
        self.item = item
        self.caption = caption
        self.stream_url  = self.compute_stream_url()

    def play_stream(self, key):
        try:
            clear_screen()
            print(f"Radio name: {self.item['title']}")
            print(f"Country: {self.item['country']}")
            print(f"Location: {self.item['location']}")
            print(f"Position: {self.item['geom']['coordinates']}")
            print("Keybindings: / to decrease vol, * to increase vol")
            print("             m to mute, space to pause, arrows to seek stream ")
            print("Press q to exit")
            print("#"*200)
            # Use subprocess to execute the MPlayer command with the stream URL
            subprocess.run(['mpv',
                            '--cache-pause-initial=yes',
                            '--cache-pause=no',
                            '--demuxer-thread=yes',
                            '--demuxer-readahead-secs=30',
                            '--framedrop=vo',
                            '--sid=1',
                            '-cache-secs=30',
                            self.stream_url])
            clear_screen()
            print("Sure to quit? press q again, or any other key to return")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 0

    def compute_stream_url(self):
        channel_id = self.item["href"].split("/")[-1]
        val = int(time.time() * 1000)
        return f"https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{val}"

    def play_radio(self, button):
        response = urwid.Text([
            u'  Selected ', u'\n',
            self.item["title"], u'\n'
        ])
        done = MenuButton(u'play', self.play_stream)
        response_box = urwid.Filler(urwid.Pile([response, done]))
        top.open_box(urwid.AttrMap(response_box, 'options'))


def clear_screen():
    subprocess.run(["clear"])

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode("utf-8")

def get_feature(d):
    feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [d['geo'][0], d['geo'][1]]}}
    feature['properties'] = {
        'title': remove_accents(d['title']),
        'country': remove_accents(d['country']),
        'location_id': d['id'],
        'lng': d['geo'][0],
        'lat': d['geo'][1]
    }
    return feature

def fetch_geojson_data(url, default_file_path):
    data = read_json_data(default_file_path)
    if data: return data
    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data_parsed = defaultdict(dict)
        rg_json = response.json()

        for item in rg_json['data']['list']:
            country = remove_accents(item['country'])
            city = remove_accents(item['title'])
            location_id = item['id']
            geom = {'type': 'Point', 'coordinates': [item['geo'][0], item['geo'][1]]}
            data_parsed[country][city] = {"id":location_id, "geometry": geom}
        write_json_data(data_parsed, default_file_path)
        return data_parsed

    except requests.exceptions.RequestException as e:
        print("Error fetching GeoJSON data:", e)
        return read_json_data(default_file_path, error=True)

def write_json_data(data, file_path):
    try:
        with open(file_path, "w") as file_open:
            file_open.write(json.dumps(data))
    except Exception as e:
        print(e)

def read_json_data(file_path, error=False):
    if not os.path.isfile(file_path): return {}
    if time.time() - os.stat(file_path).st_ctime > (24*60*60) and not error: return {}
    with open(file_path) as file_open:
        return json.load(file_open)

def exit_on_q(key):
    if key in ('q', 'Q'):
        clear_screen()
        raise urwid.ExitMainLoop()

if __name__=="__main__":
    data_parsed = fetch_geojson_data(geojson_url, default_file_path)
    if not data_parsed:
        print("error getting data")
        sys.exit()

    menu_top = SubMenu(u'Main Menu', [
        Country(
            country,
            locations)
        for country, locations in sorted(data_parsed.items())
    ])
    top = HorizontalBoxes()
    top.open_box(menu_top.menu)
    urwid.MainLoop(urwid.Filler(top, 'middle', ROW_SIZE), palette, unhandled_input=exit_on_q).run()

