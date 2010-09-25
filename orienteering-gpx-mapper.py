# coding: utf-8

"""
TODO:
    - передача входных данных
    - попробовать определять что GPS потерялся (много одинаковых точек) - отображать этот факт в комментарии
    - путь-темп по трэку
    - анализ время движения/времени стояния по кп
"""

from xml.etree import ElementTree
import datetime
from pytz import timezone, utc
import pyproj
import os
WGS84 = pyproj.Geod(ellps='WGS84')

input_gpx_path = ur"D:\My Dropbox\Speleo Library\Рогейн\2010-Балашиха-8h-half.gpx"

start_time = datetime.datetime.strptime("11:00:00", "%H:%M:%S").time()
start_date = datetime.date(2010, 9, 25)
start = datetime.datetime.combine(start_date, start_time)
start -= datetime.timedelta()
tz = timezone('Europe/Moscow')
start = tz.localize(start)

def read_time(start, s):
    hours, min, sec = s.split(":")
    hours = int(hours)
    sec = int(sec)
    min = int(min)
    #hours = min//60
    min = min % 60
    return start + datetime.timedelta(0, sec, 0, 0, min, hours)

def text_node(tag, text):
    e = ElementTree.Element(tag)
    e.text = text
    return e

def distance(p1, p2):
    # lon-lat
    return WGS84.inv(p1[0], p1[1], p2[0], p2[1])[2]

#raw_header = """
#№п/п Фамилия, имя              Коллектив            Квал Номер ГР  Результат Место Прим     1( 34)       2( 36)       3( 37)       4( 38)       5( 39)       6( 41)       7( 48)       8( 47)       9( 46)      10( 45)      11( 44)      12( 43)      13( 42)      14( 49)      15( 50)      16( 51)      17( 31)      18( 32)      19( 52)
#""".strip()
#raw_splits = """
#7:42( 90)   10:56( 83)   13:02( 81)   17:56( 76)   18:58( 74)   21:26( 65)   36:57( 89)   46:04( 89)   47:50( 90)   52:53( 90)   59:06( 89)   63:48( 87)   66:05( 88)   70:03( 86)   75:18( 86)   78:48( 86)   86:39( 87)   88:25( 88)   92:21( 89)   94:05
#""".strip()

splits = u"""
старт   00:00:00    00:00
1-44	00:07:59	07:59
2-56	00:16:32	08:33
3-26	00:32:56	16:24
4-47	00:45:32	12:36
5-81	00:57:47	12:15
6-32	01:13:05	15:18
7-58	01:21:32	08:27
8-68	01:53:35	32:03
9-92	02:06:00	12:25
10-52	02:19:42	13:42
11-52	02:19:42	00:00
12-66	02:51:08	31:26
13-34	03:05:11	14:03
14-61	03:15:33	10:22
15-65	04:15:01	59:28
16-91	04:39:39	24:38
""".strip().splitlines(False)
splits = map(lambda s: tuple(s.split()[:2]), splits)
splits = [(name, read_time(start, time)) for name, time in splits]

#raw_header = raw_header[raw_header.find('1', 20):]
#split_names = [u'старт'] + [
#    '-'.join(m.groups())
#    for m in re.finditer(r'(\d+)[(] *(\d+)[)]', raw_header)
#] + [u'финиш']
#split_times = [(start, None)] + [
#    (read_time(start, m.group(1)), m.group(2))
#    for m in re.finditer(r'(\d+:\d+)(?:[(] *(\d+)[)])?', raw_splits)
#]
#splits = zip(split_names, split_times)

doc = ElementTree.parse(input_gpx_path)

outdoc = ElementTree.ElementTree(ElementTree.Element('kml'))
outdoc_document = ElementTree.Element('Document')
outdoc.getroot().append(outdoc_document)

prev = current_ele = current_lat = current_lon = current = None
checkpoints = iter(splits)
checkpoint = next(checkpoints)
prev_cp = prev_cp_data = None

all_found = False
try:
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

        while prev <= checkpoint[1] and checkpoint[1] < current:
            position = (checkpoint[1] - prev).total_seconds() / (current - prev).total_seconds()

            if not prev_cp is None:
                dist = distance((prev_cp_data[:2]), (current_lon, current_lat))
                time = checkpoint[1] - prev_cp[1]
                comments = [
                    #str(checkpoint[1][1]) + u" место",
                    u"Время: " + str(time),
                    u"Путь (прямо): " + str(int(round(dist))) + u"м",
                    u"Темп (прямо): " + str(round(1000.0*time.total_seconds()/60.0/dist, 1)) + u" мин/км." if dist else '--',
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

            name = checkpoint[0]
            print name, 'found'
            wpt.append(text_node('name', text = name))
            wpt.append(text_node('description', text = "\n".join(comments)))

            #wpt.append(text_node('time', text = checkpoint[1][0].isoformat()))
            outdoc_document.append(wpt)

            prev_cp_data = (current_lon, current_lat, current_ele)
            prev_cp = checkpoint
            checkpoint = next(checkpoints)
            print "Looking for", checkpoint
except StopIteration:
    print "All waypoints found"
    all_found = True

if not all_found:
    raise Exception("not all points found :( aborting")

outdoc.write(
    os.path.splitext(input_gpx_path)[0] + '.checkpoints.kml',
    encoding = 'utf-8',
    xml_declaration=True
)
