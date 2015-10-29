# -*- coding: utf-8 -*-
from __future__ import division
import platform, subprocess, time, os, string
from requests import get
from teeworlds import Teeworlds

## http://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python
def is_text_file(filename):
    s=open(filename).read(512)
    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    if not s:
        # Empty files are considered text
        return True
    if "\0" in s:
        # Files with null bytes are likely binary
        return False
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_null_trans, text_characters)
    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t))/float(len(s)) > 0.30:
        return False
    return True

def host_memory_usage():
    '''
    returns a dict of host memory usage values
                    {'percent': int((used/total)*100),
                    'percent_cached':int((cached/total)*100),
                    'used': int(used/1024),
                    'total': int(total/1024)}
    '''
    
    out = open('/proc/meminfo')
    for line in out:
        if 'MemTotal:' == line.split()[0]:
            split = line.split()
            total = float(split[1])
        if 'MemFree:' == line.split()[0]:
            split = line.split()
            free = float(split[1])
        if 'Buffers:' == line.split()[0]:
            split = line.split()
            buffers = float(split[1])
        if 'Cached:' == line.split()[0]:
            split = line.split()
            cached = float(split[1])
    out.close()
    used = (total - (free + buffers + cached))
    return {'percent': int((used/total)*100),
            'percent_cached': int(((cached)/total)*100),
            'used': int(used/1024),
            'total': int(total/1024)}


def host_cpu_percent():
    '''
    returns CPU usage in percent
    '''
    
    f = open('/proc/stat', 'r')
    line = f.readlines()[0]
    data = line.split()
    previdle = float(data[4])
    prevtotal = float(data[1]) + float(data[2]) + \
        float(data[3]) + float(data[4])
    f.close()
    time.sleep(0.1)
    f = open('/proc/stat', 'r')
    line = f.readlines()[0]
    data = line.split()
    idle = float(data[4])
    total = float(data[1]) + float(data[2]) + float(data[3]) + float(data[4])
    f.close()
    intervaltotal = total - prevtotal
    percent = 100 * (intervaltotal - (idle - previdle)) / intervaltotal
    return str('%.1f' % percent)


def host_disk_usage(partition=None):
    '''
    returns a dict of disk usage values
                    {'total': usage[1],
                    'used': usage[2],
                    'free': usage[3],
                    'percent': usage[4]}
    '''
    
    if not partition:
        partition = '/'

    usage = subprocess.check_output(['df -h %s' % partition],
                                    universal_newlines=True,
                                    shell=True).split('\n')[1].split()
    return {'total': usage[1],
            'used': usage[2],
            'free': usage[3],
            'percent': usage[4]}


def host_uptime():
    '''
    returns a dict of the system uptime
            {'day': days,
            'time': '%d:%02d' % (hours,minutes)}
    '''
    
    f = open('/proc/uptime')
    uptime = int(f.readlines()[0].split('.')[0])
    minutes = int(uptime / 60 % 60)
    hours = int(uptime / 60 / 60 % 24)
    days = int(uptime / 60 / 60 / 24)
    f.close()
    return {'day': days, 
            'time': '%d:%02d' % (hours, minutes)}
    
def get_linux_distribution():
    '''
    return the System version
    '''
    
    return '%s %s' % (platform.linux_distribution()[0], platform.linux_distribution()[1])


def get_local_servers(dir):
    srvlist = []
    for r in os.listdir(dir):
        if not os.path.isfile(r):
            srvlist.append(r)
    return srvlist

def get_server_binaries(dir, gm):
    binlist = []
    for r in os.listdir('%s/%s' % (dir, gm)):
        if not is_text_file('%s/%s/%s' % (dir, gm, r)):
            binlist.append(r)
    return binlist

def get_tw_masterserver_list(address=None):
    tw = Teeworlds(timeout=2)
    tw.query_masters()
    tw.run_loop()
    
    srvlist = {'servers':[]}
    mslist = tw.serverlist.find(address=address)
    for srv in mslist:
        srvlist['servers'].append({ 'name': srv.name, 'gametype': srv.gametype, 'latency': srv.latency, 'players':srv.players, 'max_players':srv.max_players, 'map': srv.map });
    return srvlist;

def get_public_ip():
    return get('https://api.ipify.org').text
