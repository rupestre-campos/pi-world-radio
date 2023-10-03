#!/usr/bin/python3
import os
import json
import time
import sys
import urwid
import requests
import unicodedata
from collections import defaultdict
import subprocess

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



class HorizontalBoxes(urwid.Columns):
    def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

    def open_box(self, box):
        if self.contents:
            del self.contents[self.focus_position + 1:]
        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
            self.options('given', 24)))
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

class Choice(urwid.WidgetWrap):
    def __init__(self, caption, location_id, geom, country):
        super(Choice, self).__init__(
            MenuButton(caption, self.list_radios))
        self.caption = caption
        self.location_id = location_id
        self.geom = geom
        self.country = country

    def get_stations(self):
        response = requests.get(f"https://radio.garden/api/ara/content/page/{self.location_id}/channels")
        data = response.json()
        stations = []
        for item in data["data"]["content"][0]["items"]:
            item.update({"country": self.country, "location": self.caption, "geom": self.geom})
            stations.append(Station(item))
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
    def __init__(self, item):
        super(Station, self).__init__(
            MenuButton(item["title"], self.play_radio))
        self.item = item
        self.stream_url  = self.compute_stream_url()

    def play_stream(self, key):
        #print("Hit  / to decrease and * to increase volume" )
        #print("Hit space to pause, m to mute and q to quit" )
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
    feature['properties'] = {'title': remove_accents(d['title']), 'country': remove_accents(d['country']), 'location_id': d['id'], 'lng': d['geo'][0], 'lat': d['geo'][1]}
    return feature

def fetch_geojson_data(url, default_file_path):
    data = read_json_data(default_file_path)
    if data:
        import pdb; pdb.set_trace()
        return data
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad requests
        data_parsed = defaultdict(dict)
        rg_json = response.json()

        for item in rg_json['data']['list']:
            country = remove_accents(item['country'])
            city = remove_accents(item['title'])
            location_id = item['id']
            geom = {'type': 'Point', 'coordinates': [item['geo'][0], item['geo'][1]]}
            data_parsed[country][city] = {"id":location_id, "geometry": geom}
        with open(default_file_path, "w") as file_open:
            file_open.write(json.dumps(data_parsed))
        return data_parsed

    except requests.exceptions.RequestException as e:
        print("Error fetching GeoJSON data:", e)
        return read_json_data(default_file-path)

def read_json_data(file_path):
    if not os.path.isfile(file_path): return {}
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
        SubMenu(
            country,
            [
                Choice(
                    city,
                    data_parsed[country][city]["id"],
                    data_parsed[country][city]["geometry"],
                    country
                ) for city in sorted(data_parsed[country].keys())])
        for country in sorted(data_parsed.keys())
    ])
    top = HorizontalBoxes()
    top.open_box(menu_top.menu)
    urwid.MainLoop(urwid.Filler(top, 'middle', 10), palette, unhandled_input=exit_on_q).run()

