# coding: utf-8
from lib.cdrom import Cdrom
import os
import glob
from datetime import datetime
from time import sleep
from shutil import copytree
from win32api import GetVolumeInformation
import re

def cleanup_filename(s):
    return re.sub(ur'\W', '_', s, 0, re.UNICODE)

destination = ur't:\Фестиваль2010'
drive_letter = 'F'

drive_letter_ = drive_letter + ':'
drive = Cdrom(drive_letter, 120)

counter = 24
while True:
    first = True
    while True:
        root_list = glob.glob(os.path.join(drive_letter_, '*'))
        if root_list:
            break
        if first:
            print 'please insert disk'
        drive.eject()
        sleep(5)
        first = False

    disk_label = cleanup_filename(GetVolumeInformation(drive_letter_)[0])

    date = datetime.fromtimestamp(max([os.path.getmtime(f) for f in root_list]))
    subdir_name = '{:03}'.format(counter) + ' ' + date.isoformat('-').replace(':', '-') + ' ' + disk_label

    counter += 1
    dest_path = os.path.join(destination, subdir_name)
    if os.path.exists(dest_path):
        print 'WTF? already there'
        continue

    print 'copying started'
    copytree(drive_letter_, dest_path)
    print 'done'

    drive.eject()
    sleep(10)
