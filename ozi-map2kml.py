# coding: utf-8
import sys
import itertools
import re
from pprint import pprint
import os

import pyproj
WGS84 = pyproj.Geod(ellps='WGS84')

point_line_prefix = re.compile(r'Point\d{2,},.*')
point_line_delim = re.compile(r',\s*')
def parse_point_line(line):
    d = point_line_delim.split(line.rstrip())
    #    0     1    2      3  4   5     6       7  8    9     10   11   12
    # Point01,xy, 1009,  169,in, deg,  56,  634321,N,  36,  758498,E, grid,   ,           ,           ,N
    assert(d[1] == 'xy')
    assert(d[5] == 'deg')

    if not len(d[2]):
        return None

    lat = float(d[6]) + float(d[7])/60.0
    if d[8].upper() == 'S':
        lat *= -1

    lon = float(d[9]) + float(d[10])/60.0
    if d[11].upper() == 'W':
        lon *= -1

    return (float(d[2]), float(d[3]), lat, lon)

f = open(sys.argv[1], 'r')
lines = list(f.readlines())

picname = lines[1].rstrip() #name
picpath = lines[2].rstrip() #fullpath

#Pulkovo 1942 (1),,   0.0000,   0.0000,WGS 84
datum_name = lines[4].split(',', 1)[0]
datum_name = 'Everest 1956'
datum = pyproj.Geod(ellps=datum_name)
print datum_name, datum

picdims_prefix = re.compile('^IWH,Map Image Width/Height,.*')
picdims = tuple(map(float, ((
    (list(itertools.ifilter(picdims_prefix.match, lines))[0]).rstrip()
).split(','))[-2:]))

point_lines = itertools.ifilter(point_line_prefix.match, lines)
points = itertools.ifilter(None, itertools.imap(parse_point_line, point_lines)) # -> (x,y,lat,lon)

points = list(points)
import numpy as np

def solve(coord):
    data = points[coord:3+coord]
    return np.linalg.solve(
        [(p[0], p[1], 1) for p in data],
        [p[2+coord] for p in data]
    )

mapping = (solve(0), solve(1))

k = 1000
rotation = WGS84.inv(
    mapping[1][2], mapping[0][2],
    k * mapping[1][1] + mapping[1][2],
        - k * mapping[0][1] + mapping[0][2]
)[0]
pprint(rotation)

from xml.etree.ElementTree import Element, ElementTree
def text_node(tag, text):
    e = Element(tag)
    e.text = text
    return e

def get_coord(corner_u, corner_v, coord):
    corner_u *= picdims[0]
    corner_v *= picdims[1]
    return (np.array([corner_u, corner_v] + [1.]) * mapping[coord]).sum()

box = Element('LatLonBox')
for name, corner, coord in [
        ('north', (.5, 0), 0),
        ('south', (.5, 1), 0),
        ('east', (1, .5), 1),
        ('west', (0, .5), 1),
    ]:
    box.append(text_node(
        name,
        str(get_coord(corner[0], corner[1], coord))
    ))

box.append(text_node('rotation', str(rotation)))


overlay = Element('GroundOverlay')
overlay.append(text_node('name', picname))
#overlay.append(text_node('altitude', '0'))
#overlay.append(text_node('altitudeMode', 'clampToGround'))
overlay.append(box)


icon = Element('Icon')
picpath = 'L2.jpg'
icon.append(text_node('href', picpath))
overlay.append(icon)

root = Element('kml')
root.append(overlay)

doc = ElementTree(root)

doc.write(os.path.splitext(picname)[0] + '.kml', 'UTF-8', True, method = 'xml')
