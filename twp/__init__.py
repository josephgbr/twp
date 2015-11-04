# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.1.0 - Teeworlds Web Panel
##    Copyright (C) 2015  Alexandre Díaz
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU Affero General Public License as
##    published by the Free Software Foundation, either version 3 of the
##    License.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU Affero General Public License for more details.
##
##    You should have received a copy of the GNU Affero General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.    
#########################################################################################
from __future__ import division
from StringIO import StringIO
import platform, subprocess, time, os, string, re, fnmatch, tarfile
from zipfile import ZipFile
from teeworlds import Teeworlds, TWServerRequest
from netstat import netstat
from urllib import urlretrieve
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

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

def get_public_ip():
    return urlopen('http://api.ipify.org').read()

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
        if os.path.isdir('%s/%s' % (dir,r)):
            srvlist.append(r)
    return srvlist

def get_mod_binaries(dir, mod_folder):
    binlist = []
    for r in os.listdir('%s/%s' % (dir, mod_folder)):
        fullpath = '%s/%s/%s' % (dir, mod_folder, r)
        if os.path.isfile(fullpath) and not is_text_file(fullpath) and not fnmatch.filter(r, '.*'):
            binlist.append(r)
    return binlist

def get_mod_configs(dir, mod_folder):
    cfglist = []
    for r in os.listdir('%s/%s' % (dir, mod_folder)):
        fullpath = '%s/%s/%s' % (dir, mod_folder, r)
        if os.path.isfile(fullpath) and is_text_file(fullpath) and r.endswith('.conf'):
            cfglist.append(r)
    return cfglist

def get_tw_masterserver_list(address=None):
    tw = Teeworlds(timeout=2)
    tw.query_masters()
    tw.run_loop()
    
    srvlist = {'servers':[]}
    mslist = tw.serverlist.find(address=address)
    for srv in mslist:
        srvlist['servers'].append({ 'name': srv.name, 'gametype': srv.gametype, 'latency': srv.latency, 'players':srv.players, 'max_players':srv.max_players, 'map': srv.map });
    return srvlist;
    
def parse_data_config_basics(data):
    strIO = StringIO(data)
    content = strIO.readlines()
    strIO.close()
    
    emtpyfile = True if content else False
    cfgbasic = {'name': 'unnamed server', 'port':'8303', 'gametype':'DM', 'register':1, 'password':0, 'empty':emtpyfile}

    for line in content:
        objMatch = re.match("^([^#\s]+)\s([^#\r\n]+)", line)
        if objMatch:
            (varname,value) = [objMatch.group(1),objMatch.group(2)]
            if varname == 'sv_name':
                cfgbasic['name'] = value
            elif varname == 'sv_port':
                cfgbasic['port'] = value
            elif varname == 'sv_gametype':
                cfgbasic['gametype'] = value
            elif varname == 'sv_register':
                cfgbasic['register'] = value
            elif varname == 'sv_password':
                cfgbasic['password'] = 1
        
    return cfgbasic

def get_data_config_basics(fileconfig):
    try:
        cfgfile = open(fileconfig, "r")
        srvcfg = cfgfile.read()
        cfgfile.close()
    except Exception:
        srvcfg = ""
    return parse_data_config_basics(srvcfg)

def get_server_net_info(ip, servers):
    twreq = TWServerRequest(timeout=0.001)
    
    servers_info = []
    for server in servers:
        twreq.query_port(ip, int(server['port']))
        twreq.run_loop()
        servers_info.append({'netinfo':twreq.server, 'srvid':server['rowid'], 'fileconfig':server['fileconfig'], 'base_folder':server['base_folder']})
    return servers_info

def get_processes():
    return netstat()

def extract_targz(path, scratch_dir, delete=False):
    target_basename = os.path.basename(path[:-len(".tar.gz")])
    target_path = os.path.join(scratch_dir)

    try:
        tar_file = tarfile.open(path)
    except tarfile.ReadError, err:
        # Append existing Error message to new Error.
        message = ("Could not open tar file: %s\n"
                   " The file probably does not have the correct format.\n"
                   " --> Inner message: %s"
                   % (path, err))
        raise Exception(message)

    try:
        tar_file.extractall(target_path)
    finally:
        tar_file.close()
        if delete:
            os.unlink(path)

    return target_path

def extract_zip(path, scratch_dir, delete=False):
    target_basename = os.path.basename(path[:-len(".zip")])
    target_path = os.path.join(scratch_dir)

    try:
        zip_file = ZipFile(path)
    except zipfile.BadZipfile, err:
        # Append existing Error message to new Error.
        message = ("Could not open tar file: %s\n"
                   " The file probably does not have the correct format.\n"
                   " --> Inner message: %s"
                   % (path, err))
        raise Exception(message)

    try:
        zip_file.extractall(target_path)
    finally:
        zip_file.close()
        if delete:
            os.unlink(path)

    return target_path

ALLOWED_EXTENSIONS = set(['zip', 'gz'])    
def install_mod_from_url(url, dest):
    def _allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    
    matchObj = re.search(".*/([^/#]*)(#.*|$)", url)
    if not url or not _allowed_file(url) or not matchObj:
        raise Exception(u'Invalid URL')
    
    filename = '%s/%s' % (dest, matchObj.group(1))
    
    try:
        urlretrieve(url, '%s/%s' % (dest, matchObj.group(1)))
        
    except Exception, e:
        raise Exception(e)
    
    if url.endswith(".tar.gz"):
        extract_targz(filename, dest, True)
    elif url.endswith(".zip"):
        extract_zip(filename, dest, True)
    
    return True

def write_config_param(filename, param, new_value):
    replaced = False
    content = []
    
    try:
        if os.path.isfile(filename):
            cfgfile = open(filename, "r")
            content = cfgfile.readlines()
            cfgfile.close()
        
        cfgfile = open(filename, "w")
        for line in content:
            objMatch = re.match("^([^#\s]+)\s([^#\r\n]+)", line)
            if objMatch and param.lower() == objMatch.group(1).lower():
                cfgfile.write('%s %s\n' % (param, new_value))
                replaced = True
            else:
                cfgfile.write(line)
        
        if not replaced:
            cfgfile.write('%s %s\n' % (param, new_value))
        cfgfile.close()
    except Exception, e:
        raise Exception(e)
