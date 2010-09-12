# coding: utf-8
from urllib2 import urlopen
from re import search, IGNORECASE
from glob import glob
from os import path, rename, chdir, waitpid, mkdir
from subprocess import Popen
from shutil import rmtree
from sys import exit

for IDENAME, CHECKURL in (
    ('PhpStorm', 'http://confluence.jetbrains.net/display/WI/Web+IDE+EAP'),
    ('PyCharm', 'http://confluence.jetbrains.net/display/PYH/JetBrains+PyCharm+Preview'),
):
    print 'checking for updates for', IDENAME
    dists = []
    for d in glob(r'c:\Program Files\JetBrains\\'+IDENAME+'*'):
        version_file = d + r'/version.txt'
        if not path.exists(version_file):
            continue
        f = open(version_file, 'r')
        version = f.read().strip()
        f.close()
        dists.append((version, d))

    dists = dict(dists)
    print 'installed', IDENAME+'s', dists.keys()

    f = urlopen(CHECKURL)
    last_url = search('href="([^"]+'+IDENAME+'[^"]+[.]exe)"', f.read(), flags=IGNORECASE).group(1)
    print 'last '+IDENAME+':', last_url
    f.close()

    def already_installed(dists, last_url):
        for build in dists.keys():
            if build in last_url:
                return True
        return False

    if not already_installed(dists, last_url):
        version = outname = last_url.split('/')[-1]
        chdir('.downloads')
        try:
            if not path.exists(outname):
                Popen(['wget', '-O', outname + '.tmp', '--continue', last_url]).communicate()
                rename(outname + '.tmp', outname)
            else:
                print 'already downloaded'
        finally:
            chdir('..')
        
        newdir = IDENAME+'EAP'
        olddir = newdir + '.old'
        rmtree(olddir, True)
        if path.exists(newdir):
            rename(newdir, olddir)
        mkdir(newdir)
        chdir(newdir)
        
        f = open('version.txt', 'w')
        f.write(version)
        f.close()
        
        Popen([r'c:\Program Files\7-Zip\7z.exe', 'x', "../.downloads/"+outname]).communicate()
        chdir('..')
        rmtree(olddir, True)
        #Popen([newdir + '/bin/'+IDENAME+'.exe'])
        print 'all done'
    else:
        print 'up-to-date'
