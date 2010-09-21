# coding: utf-8
from xml.etree import ElementTree as e
import re
import datetime


raw_header = """
№п/п Фамилия, имя              Коллектив            Квал Номер ГР  Результат Место Прим     1( 34)       2( 36)       3( 37)       4( 38)       5( 39)       6( 41)       7( 48)       8( 47)       9( 46)      10( 45)      11( 44)      12( 43)      13( 42)      14( 49)      15( 50)      16( 51)      17( 31)      18( 32)      19( 52)
""".strip()
start = "18:06:31"
raw_splits = """
7:42( 90)   10:56( 83)   13:02( 81)   17:56( 76)   18:58( 74)   21:26( 65)   36:57( 89)   46:04( 89)   47:50( 90)   52:53( 90)   59:06( 89)   63:48( 87)   66:05( 88)   70:03( 86)   75:18( 86)   78:48( 86)   86:39( 87)   88:25( 88)   92:21( 89)   94:05
""".strip()

raw_header = raw_header[raw_header.find('1', 20):]
split_names = ['-'.join(m.groups()) for m in re.finditer(r'(\d+)[(] *(\d+)[)]', raw_header)]
split_times = [m.groups() for m in re.finditer(r'(\d+:\d+)[(] *(\d+)[)]', raw_splits)]

splits = zip(split_names, split_times)

doc = e.parse(ur"d:/My Dropbox/Speleo Library/МосМеридиан/2010-09-21 Ясенево.gpx")
prev = None
for e in doc.findall('.//{http://www.topografix.com/GPX/1/1}trkpt'):
    lat, lon = e.attrib['lat'], e.attrib['lon']
    current = e.findtext('{http://www.topografix.com/GPX/1/1}time')
    current = current[current.find('T')+1:]
    current = datetime.datetime.strptime(current, '%H:%M:%SZ')
    if prev is None:
        prev = current
        continue
    print current-prev
    break