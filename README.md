# piradio.py

## What is this?

A cli to tune-in to streaming stations from around the world provided by radio.garden, 
this project is not related to radio.garden but just provides a client to listen in old hardware as well.
Providing history and favorites, search as you type and random station functions.

A fork from original project pi-world-radio adapted to run with python on the terminal
being suitable for very old hardware. Tested in a pentium 4 single core, 1.5Gb RAM from 2000's era.
Developed in/for linux, not tested but should run ok in other OS like windows, 
for that you need to adjust likely to install mpv and make it on path.

## Installation

DEBIAN Linux
install mpv for stream play with

```sudo apt install mpv```

To save configs after exit like volume run

```
mkdir -p ~/.config/mpv/scripts && \ 
wget https://raw.githubusercontent.com/d87/mpv-persist-properties/master/persist-properties.lua \
-P ~/.config/mpv/scripts
```

Then clone repo, install python requirements and copy software to path with:

```
git clone https://github.com/rupestre-campos/pi-world-radio.git
cd pi-world-radio
python3 -m pip install -r requirements.txt
sudo cp piradio.py /usr/bin/piradio.py
# call it and enjoy 
piradio.py
```

Still work in progress.

