# pi-world-radio

## What is this?

A cli to tune-in to streaming stations from around the world.
A fork from original project pi-world-radio adapted to run with python on the terminal
being suitable for very old hardware. Tested in a pentium 4 single core, 1.5Gb RAM from 2000's era.

##Installation
install mpv for stream play with

sudo apt install mpv python3-venv

then install python requirements with
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -r requirements.txt


then run and have fun

python3 radio_cli.py


try also a version with terminal UI

python3 piradio.py

Still work in progress. Feedback and help welcome.

