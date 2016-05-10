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
import platform, subprocess, time, os, string, re, fnmatch, tarfile, zipfile, telnetlib, random, io, \
    copy
from zipfile import ZipFile, is_zipfile
from teeworlds import Teeworlds, TWServerRequest
from banned_list import BannedList
from banner_generator import BannerGenerator
from TWPConfig import TWPConfig
from netstat import netstat
from urllib import urlretrieve
from urllib2 import urlopen, URLError
from . import forms

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
    try:
        IP = urlopen('http://api.ipify.org').read()
    except URLError:
        IP = None
    return IP

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


def host_localtime():
    ltime = subprocess.check_output(['date +"%H:%M"'], universal_newlines=True, shell=True).split('\n')[0]
    return {'localtime': ltime}


def host_uptime():
    '''
    returns a dict of the system uptime
            {'day': days,
            'time': '%d:%02d' % (hours,minutes)}
    '''
    
    f = open('/proc/uptime')
    line = f.readlines()[0]
    f.close()
    uptime = int(line.split(" ")[0].split('.')[0])
    minutes = int(uptime / 60 % 60)
    hours = int(uptime / 60 / 60 % 24)
    days = int(uptime / 60 / 60 / 24)
    return {'day': days, 
            'time': '%d:%02d' % (hours, minutes)}
    
def get_linux_distribution():
    '''
    return the System version
    '''
    
    return '%s %s' % (platform.linux_distribution()[0], platform.linux_distribution()[1])


def get_local_servers(dir):
    srvlist = list()
    for r in os.listdir(dir):
        if os.path.isdir('%s/%s' % (dir,r)):
            srvlist.append(r)
    return srvlist

def get_mod_binaries(dir, mod_folder):
    binlist = list()
    for r in os.listdir('%s/%s' % (dir, mod_folder)):
        fullpath = '%s/%s/%s' % (dir, mod_folder, r)
        if os.path.isfile(fullpath) and not is_text_file(fullpath) and not fnmatch.filter(r, '.*'):
            binlist.append(r)
    return binlist if len(binlist) > 0 else None

def get_mod_maps(dir, mod_folder):
    maplist = list()
    for r in os.listdir('%s/%s/data/maps' % (dir, mod_folder)):
        fullpath = '%s/%s/data/maps/%s' % (dir, mod_folder, r)
        if os.path.isfile(fullpath) and not is_text_file(fullpath) and r.lower().endswith('.map'):
            maplist.append({'name':r[:-4], 'size': '%.2f' % (os.path.getsize(fullpath)/1024)})
    return sorted(maplist, key=lambda k: k['name']) if len(maplist) > 0 else None

def get_mod_configs(dir, mod_folder):
    cfglist = list()
    for r in os.listdir('%s/%s' % (dir, mod_folder)):
        fullpath = '%s/%s/%s' % (dir, mod_folder, r)
        if os.path.isfile(fullpath) and is_text_file(fullpath) and r.lower().endswith('.conf'):
            cfglist.append(r)
    return cfglist

def get_tw_masterserver_list(address=None):
    tw = Teeworlds(timeout=5)
    tw.query_masters()
    tw.run_loop()
    
    srvlist = {'servers':[]}
    mslist = tw.serverlist.find(address=address)
    for srv in mslist:
        srvlist['servers'].append({ 'name': srv.name, 'gametype': srv.gametype, 'latency': srv.latency, 
                                   'players':srv.players, 'max_players':srv.max_players, 'map': srv.map });
    return srvlist;
    
def parse_data_config_basics(data):
    strIO = StringIO(data)
    content = strIO.readlines()
    strIO.close()
    
    emtpyfile = True if content else False
    cfgbasic = {'name': 'unnamed server', 'port':'8303', 'gametype':'DM', 'register':1, 
                'password':0, 'logfile':None, 'econ_port':None, 'econ_pass': None,
                'empty':emtpyfile}

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
            elif varname == 'logfile':
                cfgbasic['logfile'] = value
            elif varname == 'ec_port':
                cfgbasic['econ_port'] = value
            elif varname == 'ec_password':
                cfgbasic['econ_pass'] = value
        
    return cfgbasic

def get_data_config_basics(fileconfig):
    try:
        cfgfile = io.open(fileconfig, "r")
        srvcfg = cfgfile.read()
        cfgfile.close()
    except Exception:
        srvcfg = ""
    return parse_data_config_basics(srvcfg)

def get_server_net_info(ip, servers):
    twreq = TWServerRequest(timeout=0.01)
    
    servers_info = list()
    for server in servers:
        twreq.query_port(ip, int(server.port))
        twreq.run_loop()

        servers_info.append({'netinfo':twreq.server64.version and twreq.server64 or twreq.server, 'srvid':server.id, 'fileconfig':server.fileconfig, 
                             'base_folder':server.base_folder})
    return servers_info

def search_server_pid(binpath, fileconfig):
    cmd = subprocess.check_output(['ps','-A','u'])
    for line in cmd.splitlines():
        array_line = [x for x in line.split(' ') if x !='']
        if '%s -f %s' % (binpath,fileconfig) in line:
            return int(array_line[1])
    return None

def extract_targz(path, scratch_dir, delete=False):
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

def extract_maps_package(filepath, dest, delete=False):
    counter = 0
    if tarfile.is_tarfile(filepath):
        try:
            tar_file = tarfile.open(filepath)
        except tarfile.ReadError, err:
            return False
    
        try:
            members = tar_file.getmembers()
            for tarinfo in members:
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0700
                if '/' not in tarinfo.name and tarinfo.name.lower().endswith('.map'):
                    tar_file.extract(tarinfo, dest)
                    counter+=1
        finally:
            tar_file.close()
            if delete:
                os.unlink(filepath)
    elif zipfile.is_zipfile(filepath):
        try:
            zip_file = ZipFile(filepath)
        except zipfile.BadZipfile, err:
            return False
    
        try:
            members = zip_file.namelist()
            for zipinfo in members:
                if '/' not in zipinfo and zipinfo.lower().endswith('.map'):
                    zip_file.extract(zipinfo, dest)
                    counter+=1
        finally:
            zip_file.close()
            if delete:
                os.unlink(filepath)
    else:
        return False
    
    return counter>0

ALLOWED_EXTENSIONS = set(['zip', 'gz'])    
def download_mod_from_url(url, dest):
    def _allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    
    matchObj = re.search(".*/([^/#]*)(#.*|$)", url)
    if not url or not _allowed_file(url) or not matchObj:
        raise Exception('Invalid URL')
    
    filename = '%s/%s' % (dest, matchObj.group(1))
    
    try:
        urlretrieve(url, '%s/%s' % (dest, matchObj.group(1)))
        
    except Exception, e:
        raise Exception(e)
    
    return matchObj.group(1)

def install_server_mod(filepath, dest):    
    if not check_mod_package(filepath):
        return False
    
    if tarfile.is_tarfile(filepath):
        extract_targz(filepath, dest, True)
    elif zipfile.is_zipfile(filepath):
        extract_zip(filepath, dest, True)
    return True

def check_mod_package(filepath):
    checkFolders = {'data/':False, 'data/maps/': False, 'data/mapres/': False}
    
    if tarfile.is_tarfile(filepath):
        try:
            tar_file = tarfile.open(filepath)
        except tarfile.ReadError, err:
            return False
    
        try:
            tarfiles = tar_file.getnames()
            if tarfiles and len(tarfiles) > 0:
                for file in tarfiles:
                    for chkFld in checkFolders.keys():
                        if re.search('^.+/%s' % chkFld, file):
                            checkFolders[chkFld] = True
            else:
                return False
        finally:
            tar_file.close()
    elif zipfile.is_zipfile(filepath):
        try:
            zip_file = ZipFile(filepath)
        except zipfile.BadZipfile, err:
            return False
    
        try:
            zipfiles = zip_file.namelist()
            if zipfiles and len(zipfiles) > 0:
                for file in zipfiles:
                    for chkFld in checkFolders.keys():
                        if re.search('^.+/%s' % chkFld, file):
                            checkFolders[chkFld] = True
            else:
                return False
        finally:
            zip_file.close()
    
    for chkFld in checkFolders.values():
        if not chkFld:
            return False
        
    return True
        
def write_config_param(filename, param, new_value):
    replaced = False
    content = list()
    
    try:
        if os.path.isfile(filename):
            cfgfile = io.open(filename, "r")
            content = cfgfile.readlines()
            cfgfile.close()
        
        cfgfile = io.open(filename, "w")
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
    
def send_econ_command(port, password, command):
    conn = telnetlib.Telnet('localhost', port, 5)
    conn.read_until(b'Enter password:',5)
    conn.write("{0}\n".format(password))
    conn.write("{0}\n".format(command))
    chash = generate_random_ascii_string()
    conn.write("echo {0}\n".format(chash))
    netrcv = conn.read_until(chash, 5)
    conn.write("logout\n")
    conn.close()
    
    content = netrcv.splitlines()
    content = content[3:]
    content.pop(-1)
    return '%s\n' % "\n".join(content)

# This function launch commands that need CID
def send_econ_user_action(port, password, nick, action):
    conn = telnetlib.Telnet('localhost', port, 1)
    conn.read_until(b'Enter password:', 1)
    conn.write("{0}\n".format(password))
    conn.write("status\n")
    chash = generate_random_ascii_string()
    conn.write("echo {0}\n".format(chash))
    netrcv = conn.read_until(chash, 1)
    
    cid = None
    content = netrcv.splitlines()
    for line in content:
        objMatch = re.match("^.+\sid=(\d)\s.+\sname='(.+)'\s.+$", line)
        if objMatch and nick == objMatch.group(2):
            cid = int(objMatch.group(1))
            break
            
    if not cid == None:
        if action.lower() == 'kick':
            conn.write("kick %d By admin using TWP\n" % cid)
        elif action.lower() == 'ban':
            conn.write("ban %d -1 By admin using TWP\n" % cid)
        chash = generate_random_ascii_string()
        conn.write("echo {0}\n".format(chash))
        conn.read_until(chash, 1)
    
    conn.write("logout\n")
    conn.close()
    return False if cid == None else True

def generate_random_ascii_string(size=8):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))

def get_support_languages():
    langs = list()
    for r in os.listdir('%s/translations' % os.getcwd()):
        fullpath = '%s/translations/%s' % (os.getcwd(), r)
        if os.path.isdir(fullpath):
            langs.append(r)
    return langs

# Code from: http://code.activestate.com/recipes/266466-html-colors-tofrom-rgb-tuples/
def HTMLColorToRGBA(colorstring):
    """ convert #RRGGBBAA to an (R, G, B, A) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6 and len(colorstring) != 8:
        raise ValueError, "input #%s is not in #RRGGBBAA format" % colorstring
    
    if len(colorstring) == 6:
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        a = 255
    else:
        r, g, b, a = colorstring[:2], colorstring[2:4], colorstring[4:6], colorstring[6:]
        r, g, b, a = [int(n, 16) for n in (r, g, b, a)]

    return (r, g, b, a)
##
