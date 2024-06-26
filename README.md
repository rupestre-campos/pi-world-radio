# piradio.py
![image](https://github.com/rupestre-campos/pi-world-radio/assets/51023074/64cd5522-0f31-426c-9b89-f9a6fcc99756)

## What is this?

A cli to tune-in to streaming stations from around the world provided by radio.garden, 
this project is not related to radio.garden but just provides a client to listen.
Providing some history and favorites functionality, search as you type and just press enter for random station functions.

A fork from original project pi-world-radio, thanks to nija, adapted to run with python fron the terminal.
At the end only the reversed engineering of the radio.gardem api was used, because the whole thing
was too big to a very old hardware to handle. So I made this fork in order to 
be suitable for very old hardware without any gui.


Tested in a pentium 4 single core, 1.5Gb RAM from 2000's era, a besaty for its time but too old to render a 
online map (whitout proper hacks) or webrowsers smoothly nowadays.


Developed in/for linux, not tested but should run ok in other OS like windows, 
for that you need to adjust likely to install mpv and make it on path.

Check the incredible  project that inspired this:
https://trustmeiamaninja.github.io/pi-world-radio/

I know there is a lot that can be improved but the first goal is to make it work nice on my hardware,
but feel free to ask for help or enhancements that make sense for other setups too.

## Installation

DEBIAN Linux
install mpv for stream play with

```sudo apt install mpv gdal-bin```

To mpv be able to save configs after exit like volume run the following to install a plugin

```
mkdir -p ~/.config/mpv/scripts && \ 
wget https://raw.githubusercontent.com/d87/mpv-persist-properties/master/persist-properties.lua \
-P ~/.config/mpv/scripts
```

Then clone repo, install python requirements and copy software to path with:

```
git clone https://github.com/rupestre-campos/pi-world-radio.git
cd pi-world-radio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python piradio.py
```

Still work in progress.

