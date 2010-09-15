# coding: utf-8
from urllib2 import urlopen
from re import search, IGNORECASE
from glob import glob
from os import path, rename, chdir, waitpid, mkdir, environ
from subprocess import Popen
from shutil import rmtree
from sys import exit

PF86DIR=environ['ProgramFiles']
PFDIR=PF86DIR[:-6]

JBDIR=path.join(PF86DIR, 'JetBrains')
DWDIR=path.join(JBDIR, '.downloads')

if not path.exists(JBDIR):
    mkdir(JBDIR)
if not path.exists(DWDIR):
    mkdir(DWDIR)

chdir(JBDIR)

for IDENAME, CHECKURL in (
    ('PhpStorm', 'http://confluence.jetbrains.net/display/WI/Web+IDE+EAP'),
    ('PyCharm', 'http://confluence.jetbrains.net/display/PYH/JetBrains+PyCharm+Preview'),
):
    print 'checking for updates for', IDENAME
    dists = []
    for d in glob(path.join(JBDIR, IDENAME+'*')):
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
        chdir(DWDIR)
        try:
            if not path.exists(outname):
                Popen([path.join(PF86DIR, 'GnuWin32', 'bin', 'wget'), '-O', outname + '.tmp', '--continue', last_url]).communicate()
                rename(outname + '.tmp', outname)
            else:
                print 'already downloaded'
        finally:
            chdir(JBDIR)
        
        newdir = IDENAME+'EAP'
        olddir = newdir + '.old'
        rmtree(olddir, True)
        if path.exists(newdir):
            rename(newdir, olddir)
        mkdir(newdir)
        chdir(newdir)
        
        Popen([path.join(PFDIR, '7-Zip', '7z.exe'), 'x', path.join(DWDIR, outname)]).communicate()

        f = open('version.txt', 'w')
        f.write(version)
        f.close()
        
        chdir('..')
        rmtree(olddir, True)
        Popen([newdir + '/bin/'+IDENAME+'.exe'])
        print 'all done'
    else:
        print 'up-to-date'

rmtree(DWDIR, True)
