# coding: utf-8

"""
TODO:
    - передача входных данных
    - попробовать определять что GPS потерялся (много одинаковых точек) - отображать этот факт в комментарии
    - путь-темп по трэку
    - анализ время движения/времени стояния по кп
"""

from xml.etree import ElementTree
import re
import datetime
from pytz import timezone, utc
import pyproj
import os

input_gpx_path = ur"d:/My Dropbox/Speleo Library/МосМеридиан/2010-09-21 Ясенево.gpx"
WGS84 = pyproj.Geod(ellps='WGS84')

def read_time(start, s):
    min, sec = s.split(":")
    sec = int(sec)
    min = int(min)
    hours = min//60
    min = min % 60
    return start + datetime.timedelta(0, sec, 0, 0, min, hours)
def text_node(tag, text):
    e = ElementTree.Element(tag)
    e.text = text
    return e

def distance(p1, p2):
    # lon-lat
    return WGS84.inv(p1[0], p1[1], p2[0], p2[1])[2]

start_time = datetime.datetime.strptime("18:06:31", "%H:%M:%S").time()
start_date = datetime.date(2010, 9, 21)
start = datetime.datetime.combine(start_date, start_time)
start -= datetime.timedelta()
tz = timezone('Europe/Moscow')
start = tz.localize(start)

raw_header = """
№п/п Фамилия, имя              Коллектив            Квал Номер ГР  Результат Место Прим     1( 34)       2( 36)       3( 37)       4( 38)       5( 39)       6( 41)       7( 48)       8( 47)       9( 46)      10( 45)      11( 44)      12( 43)      13( 42)      14( 49)      15( 50)      16( 51)      17( 31)      18( 32)      19( 52)
""".strip()
raw_splits = """
7:42( 90)   10:56( 83)   13:02( 81)   17:56( 76)   18:58( 74)   21:26( 65)   36:57( 89)   46:04( 89)   47:50( 90)   52:53( 90)   59:06( 89)   63:48( 87)   66:05( 88)   70:03( 86)   75:18( 86)   78:48( 86)   86:39( 87)   88:25( 88)   92:21( 89)   94:05
""".strip()

raw_header = raw_header[raw_header.find('1', 20):]
split_names = [u'старт'] + [
    '-'.join(m.groups())
    for m in re.finditer(r'(\d+)[(] *(\d+)[)]', raw_header)
] + [u'финиш']
split_times = [(start, None)] + [
    (read_time(start, m.group(1)), m.group(2))
    for m in re.finditer(r'(\d+:\d+)(?:[(] *(\d+)[)])?', raw_splits)
]

splits = zip(split_names, split_times)

doc = ElementTree.parse(input_gpx_path)

outdoc = ElementTree.ElementTree(ElementTree.Element('kml'))
outdoc_document = ElementTree.Element('Document')
outdoc.getroot().append(outdoc_document)

current_ele = current_lat = current_lon = current = None
checkpoints = iter(splits)
checkpoint = next(checkpoints)
prev_cp = prev_cp_data = None

for e in doc.findall('.//{http://www.topografix.com/GPX/1/1}trkpt'):
    prev = current
    prev_lat = current_lat
    prev_lon = current_lon
    prev_ele = current_ele

    current_lat, current_lon = float(e.attrib['lat']), float(e.attrib['lon'])
    current_ele = float(e.findtext('{http://www.topografix.com/GPX/1/1}ele'))
    current = e.findtext('{http://www.topografix.com/GPX/1/1}time')
    current = datetime.datetime.strptime(current, '%Y-%m-%dT%H:%M:%SZ')
    current = utc.localize(current)
    if prev is None:
        prev = current
        continue
    if prev == current:
        continue

    if prev <= checkpoint[1][0] and checkpoint[1][0] < current:
        position = (checkpoint[1][0] - prev).total_seconds() / (current - prev).total_seconds()

        if not prev_cp is None:
            dist = distance((prev_cp_data[:2]), (current_lon, current_lat))
            time = checkpoint[1][0] - prev_cp[1][0]
            comments = [
                str(checkpoint[1][1]) + u" место",
                u"Время: " + str(time),
                u"Путь (прямо): " + str(int(round(dist))) + u"м",
                u"Темп (прямо): " + str(round(1000.0*time.total_seconds()/60.0/dist, 1)) + u" мин/км.",
            ]
        else:
            comments = []

        wpt = ElementTree.Element('Placemark')
        point = ElementTree.Element('Point')
        point.append(text_node('coordinates', ",".join((
            str((1.0 - position) * prev_lon + position * current_lon),
            str((1.0 - position) * prev_lat + position * current_lat),
            str((1.0 - position) * prev_ele + position * current_ele),
        ))))
        wpt.append(point)

        wpt.append(text_node('name', text = checkpoint[0]))
        wpt.append(text_node('description', text = "\n".join(comments)))

        #wpt.append(text_node('time', text = checkpoint[1][0].isoformat()))
        outdoc_document.append(wpt)

        try:
            prev_cp_data = (current_lon, current_lat, current_ele)
            prev_cp = checkpoint
            checkpoint = next(checkpoints)
        except StopIteration:
            print "All waypoints found"
            break

outdoc.write(
    os.path.splitext(input_gpx_path)[0] + '.checkpoints.kml',
    encoding = 'utf-8',
    xml_declaration=True
)
