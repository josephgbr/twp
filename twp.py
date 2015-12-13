#!/usr/bin/env python
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
import twp
import subprocess, time, re, hashlib, sqlite3, os, sys, json, logging, time, signal, shutil
from io import BytesIO
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify, send_from_directory, send_file
from werkzeug import secure_filename
from flask_apscheduler import APScheduler
from flask.ext.babel import Babel, _, refresh; refresh()
from pngcanvas import *
from twp import BannedList, BannerGenerator
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


# Configuration
config = configparser.SafeConfigParser()
config.readfp(open('twp.conf'))


SECRET_KEY = b'4f54ffe39b613241ff7f864c51ea443537b7db9626969157'

BRAND_NAME = config.get('overview', 'brand_name')
BRAND_URL = config.get('overview', 'brand_url')
TWP_INFO = {
    'version': '0.1.0',
    'refresh_time': config.getint('global', 'refresh_time'),
    'brand_name': BRAND_NAME,
    'brand_url': BRAND_URL
}
DEBUG = config.getboolean('global', 'debug')
HOST = config.get('global', 'host')
PORT = config.getint('global', 'port')
THREADED = config.getboolean('global', 'threaded')
DATABASE = config.get('database', 'file')
SERVERS_BASEPATH = config.get('overview', 'servers')
SERVERS_BASEPATH = r'%s/%s' % (os.getcwd(), SERVERS_BASEPATH) if not SERVERS_BASEPATH[0] == '/' else SERVERS_BASEPATH
UPLOAD_FOLDER = '/tmp/'
MAX_CONTENT_LENGTH = config.getint('overview', 'max_upload_size') * 1024 * 1024
ALLOWED_EXTENSIONS = set(['zip', 'gz'])
LOGFILE = config.get('log', 'file')
LOGBYTES = config.getint('log', 'maxbytes')
LOGIN_MAX_TRIES = config.getint('login', 'max_tries')
LOGIN_BAN_TIME = config.getint('login', 'ban_time')
SSL = config.getboolean('global','ssl')
PKEY = config.get('ssl','pkey')
CERT = config.get('ssl','cert')
SSL = False if not os.path.isfile(PKEY) or not os.path.isfile(CERT) else SSL
SCHEDULER_VIEWS_ENABLED = True
SCHEDULER_EXECUTORS = {
    'default': {'type': 'threadpool', 'max_workers': 5}
}
JOBS = [
    {
        'id': 'analyze_all_server_instances',
        'func': '__main__:analyze_all_server_instances',
        'trigger': {
            'type': 'cron',
            'second': 30 # minimal time lapse: 1 min
        }
    }
]
BABEL_DEFAULT_LOCALE = 'en'
IP = twp.get_public_ip();


# Try create server directory if needed
if not os.path.isdir(SERVERS_BASEPATH):
    os.makedirs(SERVERS_BASEPATH)
    
    
# Global Vars
BannedList = BannedList()


# Start Flask App
app = Flask(__name__)
app.config.from_object(__name__)
babel = Babel(app)


# SQLite
def connect_db():
    '''
    SQLite3 connect function
    '''

    return sqlite3.connect(app.config['DATABASE'])

def query_db(query, args=(), one=False):
    '''
    SQLite3 query function
    '''
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
          for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


# App Callbacks
@app.before_request
def before_request():
    '''
    executes functions before all requests
    '''

    if request.view_args and 'lang_code' in request.view_args:
        g.current_lang = request.view_args['lang_code']
        request.view_args.pop('lang_code')
    BannedList.refresh()
    check_session()
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    '''
    executes functions after all requests
    '''

    if hasattr(g, 'db'):
        g.db.close()

@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits. The best match wins.
    return request.accept_languages.best_match(['es','en'])

# TODO: user!
@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone


# Routing
@app.route("/", methods=['GET'])
@app.route("/overview", methods=['GET'])
def overview():
    session['prev_url'] = request.path;
    return render_template('index.html', twp=TWP_INFO, dist=twp.get_linux_distribution(), ip=IP)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if get_login_tries() >= LOGIN_MAX_TRIES:
        flash(_('Session Banned: Can\'t login in this website! Fuck you :)', 'danger'))
        return redirect("/overview") 
    if request.method == 'POST':
        request_username = request.form['username']
        request_passwd = str_sha512_hex_encode(request.form['password'])

        current_url = session['prev_url'] if 'prev_url' in session else url_for('overview')

        user = query_db('select username from users where username=? and password=?', [request_username, request_passwd], one=True)

        if user:
            session['logged_in'] = True
            session['last_activity'] = int(time.time())
            session['username'] = user['username']
            flash(_('You are logged in!'), 'success')

            if current_url == url_for('login'):
                return redirect(url_for('overview'))
            return redirect(current_url)

        session['login_try'] = get_login_tries()+1
        session['last_login_try'] = int(time.time())
        flash(_('Invalid username or password! ({0}/{1})').format(get_login_tries(),LOGIN_MAX_TRIES), 'danger')
    return render_template('login.html', twp=TWP_INFO)

@app.route('/logout', methods=['GET'])
def logout():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('overview')
    
    session.pop('logged_in', None)
    session.pop('last_activity', None)
    session.pop('name', None)
    session.pop('prev_url', None)
    session.pop('login_try', None)
    session.pop('last_login_try', None)
    flash(_('You are logged out!'), 'success')
    
    if current_url == url_for('logout'):
        return redirect(url_for('overview'))
    return redirect(current_url)

@app.route('/about', methods=['GET'])
def about():
    session['prev_url'] = request.path;
    return render_template('about.html', twp=TWP_INFO)

@app.route('/servers', methods=['GET'])
def servers():
    session['prev_url'] = request.path;
    # By default all server are offline
    g.db.execute("UPDATE servers SET status='Stopped'")
    netstat = twp.netstat()
    for conn in netstat:
        if not conn[2]:
            continue
        (rest,base_folder,bin) = conn[2].rsplit('/', 2)
        srv = query_db('select rowid,* from servers where port=? and base_folder=? and bin=?', [conn[0],base_folder,bin], one=True)
        if srv:
            net_server_info = twp.get_server_net_info("127.0.0.1", [srv])[0]
            g.db.execute("UPDATE servers SET status='Running', name=?, gametype=? WHERE port=? and base_folder=? and bin=?", \
                         [net_server_info['netinfo'].name, net_server_info['netinfo'].gametype, conn[0], base_folder, bin])
    g.db.commit()
    return render_template('servers.html', twp=TWP_INFO, servers=twp.get_local_servers(SERVERS_BASEPATH))
    
@app.route('/server/<int:id>', methods=['GET'])
def server(id):
    session['prev_url'] = request.path;
    srv = query_db('select rowid,* from servers where rowid=?', [id], one=True)
    issues = query_db("select strftime('%d-%m-%Y %H:%M:%S',date) as date,message from issues where server_id=? ORDER BY date DESC", [id])
    issues_count = query_db('select count(rowid) as num from issues where server_id=?', [id], one=True)
    netinfo = None
    if srv:
        netinfo = twp.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
    else:
        flash(_('Server not found!'), "danger")
    return render_template('server.html', twp=TWP_INFO, ip=IP, server=srv, netinfo=netinfo, issues=issues, issues_count=issues_count['num'])

@app.route('/server/<int:id>/banner', methods=['GET'])
def generate_server_banner(id):
    srv = query_db('select rowid,* from servers where rowid=?', [id], one=True)
    if srv:
        png_image = BannerGenerator(500, 150, "test")
        
        if png_image.save():
            binfile = open('/tmp/twp_banner.png', "rb")
            return send_file(binfile,
                         attachment_filename="server_banner.png",
                         as_attachment=False)
        
@app.route('/players', methods=['GET'])
def players():
    session['prev_url'] = request.path;
    
    players = query_db("SELECT rowid,strftime('%d-%m-%Y %H:%M',create_date) as create_date, strftime('%d-%m-%Y %H:%M',last_seen_date) as last_seen_date,status,name from players ORDER BY name ASC")
    return render_template('players.html', twp=TWP_INFO, players=players)

@app.route('/maps', methods=['GET'])
def maps():
    session['prev_url'] = request.path;
    return render_template('index.html', twp=TWP_INFO)

@app.route('/settings', methods=['GET','POST'])
def settings():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            flash(_('Settings updates successfully'), 'info')
        else:
            session['prev_url'] = request.path;
        return render_template('settings.html', twp=TWP_INFO)
    else:
        flash(_('Can\'t access to settings page'), 'danger')
        return redirect(url_for('overview'))

@app.route('/install_mod', methods=['POST'])
def install_mod():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('servers')
    if 'logged_in' in session and session['logged_in']:
        if 'url' in request.form and not request.form['url'] == '':
            try:
                twp.install_mod_from_url(request.form['url'], SERVERS_BASEPATH)
            except Exception, e:
                flash(_("Error: %s") % str(e), 'danger')
            else:
                flash(_('Mod installed successfully'), 'info')
        else:  
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    fullpath = r'%s/%s' % (app.config['UPLOAD_FOLDER'], filename)
                    if filename.endswith(".tar.gz"):
                        twp.extract_targz(fullpath, SERVERS_BASEPATH, True)
                    elif filename.endswith(".zip"):
                        twp.extract_zip(fullpath, SERVERS_BASEPATH, True)
                    flash(_('Mod installed successfully'), 'info')
                    return redirect(current_url)
                else:
                    flash(_('Error: Can\'t install selected mod package'), 'danger')
            else:
                flash(_('Error: No file detected!'), 'danger')
    else:
        flash(_('Error: You haven\'t permissions for install new mods!'), 'danger')
    return redirect(current_url)

@app.route('/search', methods=['GET'])
def search():
    servers = []
    players = []
    searchword = request.args.get('r', '')

    sk = "%%%s%%" % searchword
    servers = query_db("SELECT rowid,* FROM servers WHERE name LIKE ? OR base_folder LIKE ?", [sk,sk])
    players = query_db("SELECT rowid,* FROM players WHERE name LIKE ?", [sk])
    return render_template('search.html', twp=TWP_INFO, search=searchword, servers=servers, players=players)

@app.route('/log/<int:id>/<string:code>/<string:name>', methods=['GET'])
def log(id, code, name):
    srv = query_db('select rowid,* from servers where rowid=?', [id], one=True)
    netinfo = None
    logdate = None
    if srv:
        log_file = r'%s/%s/logs/%s-%s' % (SERVERS_BASEPATH, srv['base_folder'], code, name)
        if not os.path.isfile(log_file):
            flash(_('Logfile not exists!'), "danger")
        else:
            dt = datetime.fromtimestamp(time.mktime(time.localtime(int(code, 16))))
            logdate = dt.strftime("%d-%m-%Y %H:%M:%S")
            netinfo = twp.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
    else:
        flash(_('Server not found!'), "danger")
    return render_template('log.html', twp=TWP_INFO, ip=IP, server=srv, logcode=code, logname=name, logdate=logdate)
    

@app.route('/_remove_mod', methods=['POST'])
def remove_mod():
    if 'logged_in' in session and session['logged_in']:
        if 'folder' in request.form:
            fullpath_folder = r'%s/%s' % (SERVERS_BASEPATH, request.form['folder'])
            if os.path.exists(fullpath_folder):
                servers = query_db('select rowid,* from servers where base_folder=?', [request.form['folder']])
                for srv in servers:
                    stop_server(srv['rowid'])
                    remove_server_instance(srv['rowid'],1)
                shutil.rmtree(fullpath_folder)
                return jsonify({'success':True})
            else:
                return jsonify({'error':True, 'errormsg':_('Error: Folder mod not exists!')})
        else:
            return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})
    return jsonify({'notauth':True})

@app.route('/_refresh_cpu_host')
def refresh_cpu_host():
    if 'logged_in' in session and session['logged_in']:
        return twp.host_cpu_percent()
    return jsonify({})

@app.route('/_refresh_uptime_host')
def refresh_uptime_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twp.host_uptime())
    return jsonify({})

@app.route('/_refresh_disk_host')
def refresh_disk_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twp.host_disk_usage(partition=config.get('overview', 'partition')))
    return jsonify({})

@app.route('/_refresh_memory_host')
def refresh_memory_containers():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twp.host_memory_usage())
    return jsonify({})

@app.route('/_refresh_host_localtime')
def refresh_host_localtime():
    return jsonify(twp.host_localtime())

@app.route('/_get_all_online_servers')
def get_all_online_servers():
    return jsonify(twp.get_tw_masterserver_list(IP))

@app.route('/_create_server_instance/<string:mod_folder>')
def create_server_instance(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        fileconfig = request.args.get('fileconfig')
        if not fileconfig or fileconfig == "":
            return jsonify({'error':True, 'errormsg':_('Invalid configuration file name.')})
        
        fileconfig = '%s.conf' % fileconfig
        fullpath_fileconfig = r'%s/%s/%s' % (SERVERS_BASEPATH,mod_folder,fileconfig)
        
        # Search for mod binaries, if only exists one use it
        bin = None
        srv_bins = twp.get_mod_binaries(SERVERS_BASEPATH, mod_folder)
        if len(srv_bins) == 1:
            bin = srv_bins[0]
        
        # Check if other server are using the same configuration file
        srvMatch = query_db('select rowid from servers where fileconfig=? and base_folder=?', [fileconfig,mod_folder], one=True)
        if srvMatch:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exits two servers with the same configuration file.<br/>Please change configuration file name and try again.")})
                    
        cfgbasic = twp.get_data_config_basics(fullpath_fileconfig)
        
        # Check if the logfile are be using by other server with the same base_folder
        srvMatch = query_db('select rowid from servers where base_folder=? and logfile=?', [mod_folder, cfgbasic['logfile']], one=True)
        if srvMatch:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exits two servers with the same log file.<br/>Please check configuration and try again.")})
            
        # Check if the econ_port are be using by other server
        srvMatch = query_db('select rowid from servers where econ_port=?', [cfgbasic['econ_port']], one=True)
        if srvMatch:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exits two servers with the same 'ec_port'.<br/>Please check configuration and try again.")})
        
        # Check if the port are be using by other server with the same base_folder
        fport = int(cfgbasic['port'])
        while True:
            srvMatch = query_db('select rowid from servers where base_folder=? and port=?', [mod_folder, str(fport)], one=True)
            if not srvMatch:
                break
            fport += 1

        try:
            if cfgbasic['name'] == 'unnamed server':
                cfgbasic['name'] = "Server created with Teeworlds Web Panel"
                twp.write_config_param(fullpath_fileconfig, "sv_name", cfgbasic['name'])
            if not fport == int(cfgbasic['port']):
                cfgbasic['port'] = str(fport)
                twp.write_config_param(fullpath_fileconfig, "sv_port", cfgbasic['port'])
        except Exception, e:
             return jsonify({'error':True, 'errormsg':str(e)})
            
        # If all checks good, create the new instance
        g.db.execute("INSERT INTO servers (fileconfig,base_folder,bin,port,name,gametype,register,logfile,econ_port,econ_password) \
                      VALUES (?,?,?,?,?,?,?,?,?,?)",
                     [fileconfig, mod_folder, bin, str(fport), cfgbasic['name'], cfgbasic['gametype'], cfgbasic['register'], cfgbasic['logfile'],
                      cfgbasic['econ_port'], cfgbasic['econ_pass']])
        g.db.commit()
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@app.route('/_remove_server_instance/<int:id>/<int:delconfig>')
def remove_server_instance(id, delconfig=0):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db("SELECT base_folder,fileconfig FROM servers WHERE rowid=?", [id], one=True)
        if not srv:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        
        if delconfig == 1:
            os.unlink(r'%s/%s/%s' % (SERVERS_BASEPATH,srv['base_folder'],srv['fileconfig']))
        
        # The problems of not use a relational database :D
        g.db.execute("DELETE FROM servers WHERE rowid=?", [id])
        g.db.execute("DELETE FROM issues WHERE server_id=?", [id])
        g.db.execute("DELETE FROM players_server WHERE server_id=?", [id])
        g.db.commit()
        
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@app.route('/_set_server_binary/<int:id>/<string:binfile>')
def set_server_binary(id, binfile):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db('select base_folder from servers where rowid=?', [id], one=True)
        # Check that is a correct binary name (exists in mod folder)
        srv_bins = twp.get_mod_binaries(SERVERS_BASEPATH, srv['base_folder'])
        if binfile in srv_bins:
            g.db.execute("UPDATE servers SET bin=? WHERE rowid=?", [binfile, id])
            g.db.commit()
            return jsonify({'success':True})
        return jsonify({'invalidBinary':True})
    return jsonify({'notauth':True})

@app.route('/_save_server_config', methods=['POST'])
def save_server_config():
    if 'logged_in' in session and session['logged_in']:
        srvid = int(request.form['srvid'])
        alaunch = 1 if 'alsrv' in request.form and request.form['alsrv'] == 'on' else 0;
        srvcfg = request.form['srvcfg'];
        srv = query_db('select fileconfig,base_folder from servers where rowid=?', [srvid], one=True)
        if srv:
            cfgbasic = twp.parse_data_config_basics(srvcfg)
            
            srvMatch = query_db('select rowid from servers where base_folder=? and port=? and rowid<>?',
                                [srv['base_folder'], cfgbasic['port'], srvid], one=True)
            if srvMatch:
                return jsonify({'error':True, \
                                'errormsg':_("Can't exits two servers with the same 'sv_port' in the same MOD.<br/>Please check configuration and try again.")})
                
            # Check if the logfile are be using by other server with the same base_folder
            srvMatch = query_db('select rowid from servers where base_folder=? and logfile=? and rowid<>?', 
                                [srv['base_folder'], cfgbasic['logfile'], srvid], one=True)
            if srvMatch:
                return jsonify({'error':True, 
                                'errormsg':_("Can't exits two servers with the same log file.<br/>Please check configuration and try again.")})
            
            g.db.execute("UPDATE servers SET alaunch=?,port=?,name=?,gametype=?,register=?,password=?,logfile=?,\
                                  econ_port=?,econ_password=? WHERE rowid=?",
                         [alaunch, cfgbasic['port'], cfgbasic['name'], cfgbasic['gametype'], cfgbasic['register'], \
                          cfgbasic['password'], cfgbasic['logfile'], cfgbasic['econ_port'], cfgbasic['econ_pass'], srvid])
            g.db.commit()
            try:
                cfgfile = open(r'%s/%s/%s' % (SERVERS_BASEPATH,srv['base_folder'],srv['fileconfig']), "w")
                cfgfile.write(srvcfg)
                cfgfile.close()
            except IOError as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            res = {'success':True, 'cfg':cfgbasic, 'id':srvid}
            res.update(cfgbasic)
            return jsonify(res)
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_config/<int:id>')
def get_server_config(id):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db('select alaunch,fileconfig,base_folder from servers where rowid=?', [id], one=True)
        if srv:
            fullpath_fileconfig = r'%s/%s/%s' % (SERVERS_BASEPATH,srv['base_folder'],srv['fileconfig'])
            (filename, rest) = srv['fileconfig'].split('.', 1)
            if os.path.exists(fullpath_fileconfig):
                try:
                    cfgfile = open(fullpath_fileconfig, "r")
                    srvcfg = cfgfile.read()
                    cfgfile.close()
                except IOError as e:
                    srvcfg = str(e)
            else:
                srvcfg = ""
            return jsonify({'success':True, 'alsrv':srv['alaunch'], 'srvcfg':srvcfg, 'fileconfig':filename})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_get_mod_configs/<string:mod_folder>')
def get_mod_configs(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        jsoncfgs = {'configs':[]}
        cfgs = twp.get_mod_configs(SERVERS_BASEPATH, mod_folder)
        for config in cfgs:
            srv = query_db('select rowid from servers where fileconfig=? and base_folder=?', [config,mod_folder], one=True)
            if not srv:
                jsoncfgs['configs'].append(os.path.splitext(config)[0])
        return jsonify(jsoncfgs)
    return jsonify({'notauth':True})

@app.route('/_start_server_instance/<int:id>')
def start_server(id):
    if 'logged_in' in session and session['logged_in']:        
        srv = query_db('select rowid,* from servers WHERE rowid=?', [id], one=True)
        if srv:
            if not srv['bin']:
                return jsonify({'error':True, 'errormsg':_('Undefined server binary file!!')})
            
            srvMatch = query_db("select rowid from servers WHERE status='Running' and port=?", [srv['port']], one=True)
            if srvMatch:
                return jsonify({'error':True, 'errormsg':_('Can\'t run two servers in the same port!')})
            
            try:
                start_server_instance(srv['base_folder'], srv['bin'], srv['fileconfig'])
            except Exception, e:
                return jsonify({'error':True, 'errormsg':str(e)})
            
            time.sleep(1) # Be nice with the server...
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_stop_server_instance/<int:id>', methods=['POST'])
def stop_server(id):
    if 'logged_in' in session and session['logged_in']:
        server = query_db("SELECT port,base_folder,bin FROM servers WHERE rowid=?", [id], one=True)
        if server:
            netstat = twp.netstat()
            for conn in netstat:
                if conn[0] == server['port'] and conn[2].endswith('%s/%s' % (server['base_folder'],server['bin'])):
                    try:
                        os.kill(int(conn[1]), signal.SIGTERM)
                    except Exception, e:
                        return jsonify({'error':True, 'errormsg':_('System failure: {0}').format(str(e))})
                    else:
                        return jsonify({'success':True})
                    break
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Can\'t found server pid')})
        else:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_instances_online')
def get_server_instances_online():
    servers = query_db("SELECT rowid FROM servers WHERE status='Running'")
    return jsonify({'success':True, 'num':len(servers)})

#@app.route('/_reboot')
#def reboot():
#    if 'logged_in' in session and session['logged_in']:
#        shutdown_all_server_instances()
#        
#        try:
#            subprocess.check_call("/sbin/shutdown -r now 'Reboot called by TWP'", shell=True)
#        except:
#            return jsonify({ 'error':True, 'errormsg':u"Can't reboot system!<br/><span class='text-muted'>need root privileges</span>"})
#        return jsonify({'success':True })
#    return jsonify({'notauth':True})

@app.route('/_get_server_instance_log/<int:id>/<int:seek>', methods=['POST'])
def get_current_server_instance_log(id, seek):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db("SELECT port,base_folder,bin,logfile FROM servers WHERE rowid=?", [id], one=True)
        if srv:
            logcontent = ""
            if not srv['logfile']:
                return jsonify({'error':True, 'errormsg':_('Logfile not defined!')})
            try:
                if srv['logfile'][0] == '/':
                    fullpath = srv['logfile']
                else:
                    fullpath = r'%s/%s/%s' % (SERVERS_BASEPATH,srv['base_folder'],srv['logfile'])
                
                file_size = os.path.getsize(fullpath)
                if seek >= file_size:
                    return jsonify({'success':True, 'content':None, 'seek':file_size})
                
                cfgfile = open(fullpath, "r")
                cfgfile.seek(seek)
                logcontent = cfgfile.read()
                logseek = cfgfile.tell()
                cfgfile.close()
            except Exception, e:
                return jsonify({'success':True, 'content':None, 'seek':0})
            
            lines = logcontent.splitlines()
            logcontent = []
            for line in lines:
                objMatch = re.match('^\[(.+)\]\[(.+)\]:\s(.+)$',line)
                if objMatch:
                    (date,section,message) = [int(objMatch.group(1), 16),objMatch.group(2),objMatch.group(3)]
                    dt = datetime.fromtimestamp(time.mktime(time.localtime(date)))
                    type = None
                    if re.match("^(?:client dropped|(?:.+\s)?failed)", message, re.IGNORECASE):
                        type = 'danger'
                    elif re.match("^No such command", message, re.IGNORECASE):
                        type = 'warning'
                    elif re.match("^(?:player is ready|player has entered the game|loading done|client accepted|cid=\d authed)", message, re.IGNORECASE):
                        type = 'success'
                    logcontent.append({'date':dt.strftime("%d-%m-%Y %H:%M:%S"),'section':section,'message':message,'type':type})
            
            return jsonify({'success':True, 'content':logcontent, 'seek':logseek})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_instance_log/<int:id>/<string:code>/<string:name>', methods=['POST'])
def get_selected_server_instance_log(id, code, name):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db("SELECT base_folder FROM servers WHERE rowid=?", [id], one=True)
        if srv:
            logcontent = ""
            log_file = r'%s/%s/logs/%s-%s' % (SERVERS_BASEPATH, srv['base_folder'], code, name)
            if not os.path.isfile(log_file):
                return jsonify({'error':True, 'errormsg':_('Logfile not exists!')})
            try:                                
                cfgfile = open(log_file, "r")
                logcontent = cfgfile.read()
                cfgfile.close()
            except Exception, e:
                return jsonify({'success':True, 'content':None})
            
            lines = logcontent.splitlines()
            logcontent = []
            for line in lines:
                objMatch = re.match('^\[(.+)\]\[(.+)\]:\s(.+)$',line)
                if objMatch:
                    (date,section,message) = [int(objMatch.group(1), 16),objMatch.group(2),objMatch.group(3)]
                    dt = datetime.fromtimestamp(time.mktime(time.localtime(date)))
                    type = None
                    if re.match("^(?:client dropped|(?:.+\s)?failed)", message, re.IGNORECASE):
                        type = 'danger'
                    elif re.match("^No such command", message, re.IGNORECASE):
                        type = 'warning'
                    elif re.match("^(?:player is ready|player has entered the game|loading done|client accepted|cid=\d authed)", message, re.IGNORECASE):
                        type = 'success'
                    logcontent.append({'date':dt.strftime("%d-%m-%Y %H:%M:%S"),'section':section,'message':message,'type':type})
            
            return jsonify({'success':True, 'content':logcontent})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@app.route('/_send_econ_command', methods=['POST'])
def send_econ_command():
    if 'logged_in' in session and session['logged_in']:
        if not 'srvid' in request.form or not request.form['srvid']:
            return jsonify({'error':True, 'errormsg':'Server not defined!'})
        
        if not 'cmd' in request.form or not request.form['cmd']:
            return jsonify({'error':True, 'errormsg':'ECon command not defined!'})
        
        srvid = request.form['srvid']
        srv = query_db("SELECT econ_port,econ_password FROM servers WHERE rowid=?", [srvid], one=True)
        if srv and srv['econ_port'] and srv['econ_password']:
            econ_cmd = request.form['cmd']
            rcv = ''
            try:
                rcv = twp.send_econ_command(int(srv['econ_port']), srv['econ_password'], econ_cmd)
            except Exception, e:
                return jsonify({'error':True, 'errormsg':str(e)})
            return jsonify({'success':True, 'rcv':rcv})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found or econ not configured!')})
    return jsonify({'notauth':True})

@app.route('/_kick_player/<int:id>', methods=['POST'])
@app.route('/_ban_player/<int:id>', methods=['POST'])
def kick_ban_player(id):
    if 'logged_in' in session and session['logged_in']:
        if not 'nick' in request.form or not request.form['nick']:
            return jsonify({'error':True, 'errormsg':_('Client player not defined!')})
        
        srv = query_db("SELECT econ_port,econ_password FROM servers WHERE rowid=?", [id], one=True)
        if srv and srv['econ_port'] and srv['econ_password']:
            nick = request.form['nick']
            action = 'ban' if request.path.startswith('/_ban_player/') else 'kick' 
            try:
                if not twp.send_econ_user_action(int(srv['econ_port']), srv['econ_password'], nick, action):
                    return jsonify({'error':True, 'errormsg':_('Can\'t found \'{0}\' player!').format(nick)})         
            except Exception, e:
                return jsonify({'error':True, 'errormsg':str(e)})
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found or econ not configured!')})
    return jsonify({'notauth':True})    

@app.route('/_get_chart_values/<string:chart>', methods=['POST'])
@app.route('/_get_chart_values/<string:chart>/<int:id>', methods=['POST'])
def get_chart_values(chart, id=None):
    labels = {}
    values = {}
    if chart.lower() == 'server':
        query_data = query_db("SELECT count(DISTINCT name) as num, strftime('%Y-%m-%d', tblA.dd) as date \
            FROM  (SELECT date('now', 'localtime') as dd \
            UNION SELECT date('now', 'localtime', '-1 day') \
            UNION SELECT date('now', 'localtime', '-2 day') \
            UNION SELECT date('now', 'localtime', '-3 day') \
            UNION SELECT date('now', 'localtime', '-4 day') \
            UNION SELECT date('now', 'localtime', '-5 day') \
            UNION SELECT date('now', 'localtime', '-6 day')) as tblA \
            LEFT JOIN players_server as tblB \
            ON strftime('%d-%m-%Y',tblB.date) = strftime('%d-%m-%Y',tblA.dd) AND tblB.server_id=? \
            GROUP BY strftime('%d-%m-%Y', tblA.dd)", [id])
        if query_data:
            labels['players7d'] = []
            values['players7d'] = []
            for value in query_data:
                labels['players7d'].append(value['date'])
                values['players7d'].append(value['num'])
        else:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        
        query_data = query_db("SELECT count(clan) as num, clan FROM (SELECT DISTINCT name,clan,server_id FROM players_server \
                WHERE clan NOT NULL) WHERE server_id=? GROUP BY clan ORDER BY num DESC LIMIT 5", [id])
        if query_data:
            labels['topclan'] = []
            values['topclan'] = []
            for value in query_data:
                labels['topclan'].append(value['clan'])
                values['topclan'].append(value['num'])
                
        query_data = query_db("SELECT count(country) as num, country FROM (SELECT DISTINCT name,country,server_id FROM players_server \
                WHERE clan NOT NULL) WHERE server_id=? GROUP BY country ORDER BY num DESC LIMIT 5", [id])
        if query_data:
            labels['topcountry'] = []
            values['topcountry'] = []
            for value in query_data:
                labels['topcountry'].append(value['country'])
                values['topcountry'].append(value['num'])
            
        return jsonify({'success':True, 'values':values, 'labels':labels})
    elif chart.lower() == 'machine':
        query_data = query_db("SELECT count(DISTINCT name) as num, strftime('%Y-%m-%d', tblA.dd) as date \
            FROM  (SELECT date('now', 'localtime') as dd \
            UNION SELECT date('now', 'localtime', '-1 day') \
            UNION SELECT date('now', 'localtime', '-2 day') \
            UNION SELECT date('now', 'localtime', '-3 day') \
            UNION SELECT date('now', 'localtime', '-4 day') \
            UNION SELECT date('now', 'localtime', '-5 day') \
            UNION SELECT date('now', 'localtime', '-6 day')) as tblA \
            LEFT JOIN players_server as tblB \
            ON strftime('%d-%m-%Y',tblB.date) = strftime('%d-%m-%Y',tblA.dd) \
            GROUP BY strftime('%d-%m-%Y', tblA.dd)")
        if query_data:
            labels['players7d'] = []
            values['players7d'] = []
            for value in query_data:
                labels['players7d'].append(value['date'])
                values['players7d'].append(value['num'])
        return jsonify({'success':True, 'values':values, 'labels':labels})
    return jsonify({'error':True, 'errormsg':_('Undefined Chart!')})

@app.route('/_set_user_password/<int:id>', methods=['POST'])
def set_user_password(id):
    if 'logged_in' in session and session['logged_in']:
        if 'pass_new' in request.form and 'pass_old' in request.form:
            rows = g.db.execute("UPDATE users SET password=? WHERE rowid=? AND password=?",[str(request.form['pass_new']), id, str_sha512_hex_encode(str(request.form['pass_old']))])
            if rows.rowcount > 0:
                g.db.commit()
                return jsonify({'success':True})
            return jsonify({'error':True, 'errormsg':_('Error: Can\'t change admin password. Check settings and try again.')})
        else:
            return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})
    return jsonify({'notauth':True})


# Security Checks
def check_session():
    if 'logged_in' in session and session.get('last_activity') is not None:
        now = int(time.time())
        limit = now - 60 * config.getint('session', 'time')
        last_activity = session.get('last_activity')
        if last_activity < limit:
            flash(_('Session timed out!'), 'info')
            logout()
        else:
            session['last_activity'] = now

# Context Processors
@app.context_processor
def utility_processor():
    def get_mod_instances(mod_folder):
        servers = query_db('select rowid,* from servers where base_folder=?', [mod_folder])
        return servers
    def get_mod_binaries(mod_folder):
        return twp.get_mod_binaries(SERVERS_BASEPATH, mod_folder)
    return dict(get_mod_instances=get_mod_instances, 
                get_mod_binaries=get_mod_binaries)


# Jobs
def analyze_all_server_instances():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    
    # By default all are offline
    g.db.execute("UPDATE players SET status=0")
    # By default all servers are offline
    g.db.execute("UPDATE servers SET status='Stopped'")
    
    # Check Server & Player Status
    netstat = twp.netstat()
    for conn in netstat:
        if not conn[2]:
            continue
        objMatch = re.match("^.+\/([^\/]+)\/(.+)$", conn[2])
        if objMatch:
            (base_folder,bin) = [objMatch.group(1), objMatch.group(2)]
            srv = query_db("SELECT rowid,* FROM servers WHERE port=? AND base_folder=? AND bin=?", [conn[0], base_folder, bin], one=True)
            if srv:
                g.db.execute("UPDATE servers set status='Running' where rowid=?", [srv['rowid']])
                netinfo = twp.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
                for player in netinfo.playerlist:
                    g.db.execute("INSERT INTO players_server (server_id,name,clan,country,date) VALUES (?,?,?,?,datetime('now', 'localtime'))",
                                [srv['rowid'], player.name, player.clan, player.country])
                    
                    playerMatch = query_db('select * from players where lower(name)=?', [player.name.lower()], one=True)
                    if not playerMatch:
                        g.db.execute("INSERT INTO players (name,create_date,last_seen_date,status) VALUES (?,datetime('now', 'localtime'),datetime('now', 'localtime'),1)",
                                     [player.name])
                    else:
                        g.db.execute("UPDATE players SET last_seen_date=datetime('now', 'localtime'), status=1 WHERE lower(name)=?",
                                     [player.name.lower()])
                    
    # Reopen Offline Servers
    servers = query_db("SELECT rowid,* FROM servers WHERE status='Stopped' and alaunch=1")
    for server in servers:            
        if not os.path.isfile(r'%s/%s/%s' % (SERVERS_BASEPATH, server['base_folder'], server['bin'])):
            g.db.execute("INSERT INTO issues (server_id,date,message) VALUES (?,datetime('now', 'localtime'),?)", [server['rowid'], _('Server binary not found')])
            continue
        
        current_time_hex = hex(int(time.time())).split('x')[1]
        logs_folder = r'%s/%s/logs' % (SERVERS_BASEPATH, server['base_folder'])
        log_file = r'%s/%s/%s' % (SERVERS_BASEPATH, server['base_folder'], server['logfile'])
        # Create logs folder if not exists
        if not os.path.isdir(logs_folder):
            os.makedirs(logs_folder)
        # Move current log to logs folder
        if os.path.isfile(log_file):
            shutil.move(log_file, r'%s/%s-%s' % (logs_folder, current_time_hex, server['logfile']))
        # Report issue
        g.db.execute("INSERT INTO issues (server_id,date,message) VALUES (?,datetime('now', 'localtime'),?)", 
                     [server['rowid'], 
                     "%s <a class='btn btn-xs btn-primary pull-right' href='/log/%d/%s/%s'>View log</a>" % (_('Server Offline'), server['rowid'], current_time_hex, server['logfile'])])
        # Open server
        start_server_instance(server['base_folder'], server['bin'], server['fileconfig']) 
    
    g.db.commit()
            
    if hasattr(g, 'db'):
        g.db.close()


# Tools
def str_sha512_hex_encode(strIn):
    return hashlib.sha512(strIn.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
def shutdown_all_server_instances():
    netstat = twp.netstat()
    for conn in netstat:
        servers = query_db("SELECT base_folder,bin FROM servers WHERE port=?", [conn[0]])
        for srv in servers:
            if conn[2].endswith('%s/%s' % (server['base_folder'],server['bin'])):
                os.kill(int(conn[1]), signal.SIGTERM)

# TODO: Open how a parent not child...
def start_server_instance(base_folder, bin, fileconfig):
    subprocess.Popen([r'%s/%s/%s' % (SERVERS_BASEPATH, base_folder, bin), '-f', fileconfig],
                    shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=r'%s/%s' % (SERVERS_BASEPATH, base_folder))

def get_login_tries():
    return int(session.get('login_try')) if 'login_try' in session else 0


# Start Scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


# Init Module
if __name__ == "__main__":
    if len(LOGFILE) > 0:
        handler = RotatingFileHandler(LOGFILE, maxBytes=LOGBYTES, backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    if app.config['SSL']: 
        from OpenSSL import SSL
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(app.config['PKEY'])
        context.use_certificate_file(app.config['CERT'])
        app.run(host=app.config['HOST'], port=app.config['PORT'], threaded=app.config['THREADED'], ssl_context=context)
    else:
        app.run(host=app.config['HOST'], port=app.config['PORT'], threaded=app.config['THREADED'])
        
    #shutdown_all_server_instances()
