# piradio.py

## What is this?

A cli to tune-in to streaming stations from around the world provided by radio.garden, 
this project is not related to radio.garden but just provides a client to listen in old hardware as well.
Providing history and favorites, search as you type and random station functions.

A fork from original project pi-world-radio adapted to run with python on the terminal
being suitable for very old hardware. Tested in a pentium 4 single core, 1.5Gb RAM from 2000's era.
Developed for Debian linux but may run everywhere with proper adjustment

##Installation
install mpv for stream play with

```sudo apt install mpv```


To use with virtualenv
```sudo apt install python3-venv```

then install python requirements with
```
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -r requirements.txt
```

then run and have fun

```python3 piradio.py```

Still work in progress. Feedback and help welcome.

