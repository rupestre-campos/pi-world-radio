# Raspberry Pi Retro World Radio

<picture>
  <img src="https://github.com/trustMeIAmANinja/pi-world-radio/blob/main/docs/assets/img/retro_pi_world_radio_hero.jpg" />
</picture>

## What is this?

A retro radio to tune-in to streaming stations from around the world.

## Looking for Docs?

The build docs are here: [https://trustmeiamaninja.github.io/pi-world-radio](https://trustmeiamaninja.github.io/pi-world-radio)

## Notes to this fork
Gpio control has been deactivated for now, but keyboard keys h, l control sound up and down, and arrows to move map.
Modified version with a fastapi server instead of node js one for better compatibility with older systems running debian, 
I am talking about a pentium 4 single 2.8Ghz core with 1.5Gb ram and 40Gb Hdd notebook.

The map was converted to mapbox.js only without the gl part for old systems.
Even like this it was too much for  the map to work so, i decided to make a cli to run the music streams, and seems to work.
Still work in progress.

