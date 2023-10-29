import fiona
import gj2ascii

# to create world ascii art
# create your own and update function in main script to update

countries = "countries.geojson"
file_path = "world_ascii.txt"

width = 110
asc = []

with fiona.open(countries, "r") as poly:
    asc.append(gj2ascii.render(poly, width, char=".", fill=" ", bbox=(-180,-90,180,90), all_touched=False))

with open(file_path, "w") as f:
    f.write(''.join(asc))
