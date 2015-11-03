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
import subprocess, time, re, hashlib, sqlite3, os, json, logging, time, signal
from logging.handlers import RotatingFileHandler
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify, send_from_directory
from werkzeug import secure_filename
from flask_apscheduler import APScheduler
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


# Configuration
config = configparser.SafeConfigParser()
config.readfp(open('twp.conf'))


SECRET_KEY = b'4f54ffe39b613241ff7f864c51ea443537b7db9626969157'

TWP_INFO = {
    'version': '0.1.0',
    'refresh_time': config.getint('global', 'refresh_time')
}
DEBUG = config.getboolean('global', 'debug')
HOST = config.get('global', 'host')
PORT = config.getint('global', 'port')
THREADED = config.getboolean('global', 'threaded')
DATABASE = config.get('database', 'file')
SERVERS_BASEPATH = config.get('overview', 'servers')
UPLOAD_FOLDER = '/tmp/'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['zip', 'gz'])
LOGFILE = config.get('log', 'file')
LOGBYTES = config.getint('log', 'maxbytes')
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
        'id': 'relaunch_servers_offline',
        'func': '__main__:relaunch_servers_offline',
        'trigger': {
            'type': 'cron',
            'second': 30 # minimal time lapse: 1 min
        }
    }
]
    
IP = twp.get_public_ip();



# Start Flask App
app = Flask(__name__)
app.config.from_object(__name__)

if not os.path.isdir(SERVERS_BASEPATH):
    os.makedirs(SERVERS_BASEPATH)

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

    check_session_limit()
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    '''
    executes functions after all requests
    '''

    if hasattr(g, 'db'):
        g.db.close()


# Routing
@app.route("/")
@app.route("/overview")
def overview():
    session['prev_url'] = request.path;
    return render_template('index.html', twp=TWP_INFO, dist=twp.get_linux_distribution(), ip=IP)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        app.logger.debug('A value for debugging')
        request_username = request.form['username']
        request_passwd = str_sha512_hex_encode(request.form['password'])

        current_url = session['prev_url'] if 'prev_url' in session else url_for('overview')

        user = query_db('select username from users where username=? and password=?', [request_username, request_passwd], one=True)

        if user:
            session['logged_in'] = True
            session['last_activity'] = int(time.time())
            session['username'] = user['username']
            flash(u'You are logged in!', 'success')

            if current_url == url_for('login'):
                return redirect(url_for('overview'))
            return redirect(current_url)

        flash(u'Invalid username or password!', 'danger')
    return render_template('login.html', twp=TWP_INFO)

@app.route('/logout')
def logout():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('overview')
    
    session.pop('logged_in', None)
    session.pop('last_activity', None)
    session.pop('name', None)
    session.pop('prev_url', None)
    flash(u'You are logged out!', 'success')
    
    if current_url == url_for('logout'):
        return redirect(url_for('overview'))
    return redirect(current_url)

@app.route('/about')
def about():
    session['prev_url'] = request.path;
    return redirect(url_for('overview'))

@app.route('/servers')
def servers():
    session['prev_url'] = request.path;
    check_servers_status()
    return render_template('servers.html', twp=TWP_INFO, servers=twp.get_local_servers(SERVERS_BASEPATH))

@app.route('/players')
def players():
    session['prev_url'] = request.path;
    
    players = query_db("SELECT rowid,* from players ORDER BY name ASC")
    return render_template('players.html', twp=TWP_INFO, players=players)

@app.route('/maps')
def maps():
    session['prev_url'] = request.path;
    return render_template('index.html', twp=TWP_INFO)

@app.route('/settings', methods=['GET','POST'])
def settings():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            flash(u'Settings updates successfully', 'info')
        else:
            session['prev_url'] = request.path;
        return render_template('settings.html', twp=TWP_INFO)
    else:
        flash(u'Can\'t access to settings page', 'danger')
        return redirect(url_for('overview'))

@app.route('/install_mod', methods=['POST'])
def install_mod():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('servers')
    if 'logged_in' in session and session['logged_in']:
        if 'url' in request.form and not request.form['url'] == '':
            try:
                twp.install_mod_from_url(request.form['url'], SERVERS_BASEPATH)
            except Exception, e:
                flash("Error: %s" % str(e), 'danger')
            else:
                flash(u'Mod installed successfully', 'info')
        else:  
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    
                    app.logger.info("Extract: %s" % filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    fullpath = '%s/%s' % (app.config['UPLOAD_FOLDER'], filename)
                    if filename.endswith(".tar.gz"):
                        twp.extract_targz(fullpath, SERVERS_BASEPATH, True)
                    elif filename.endswith(".zip"):
                        twp.extract_zip(fullpath, SERVERS_BASEPATH, True)
                    flash(u'Mod installed successfully', 'info')
                    return redirect(current_url)
                else:
                    flash(u'Error: Can\'t install selected mod package', 'danger')
            else:
                flash(u'Error: No file detected!', 'danger')
    else:
        flash(u'Error: You haven\'t permissions for install new mods!', 'danger')
    return redirect(current_url)


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

@app.route('/_get_all_online_servers')
def get_all_online_servers():
    return jsonify(twp.get_tw_masterserver_list(IP))

@app.route('/_create_server_instance/<string:mod_folder>')
def create_server_instance(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        fileconfig = request.args.get('fileconfig')
        if not fileconfig or fileconfig == "":
            return jsonify({'error':True, 'errormsg':u'Invalid configuration file name.'})
        
        # Search for mod binaries, if only exists one use it
        bin = None
        srv_bins = twp.get_mod_binaries(SERVERS_BASEPATH, mod_folder)
        if len(srv_bins) == 1:
            bin = srv_bins[0]
        
        fullpath_fileconfig = '%s/%s/%s.conf' % (SERVERS_BASEPATH,mod_folder, fileconfig)
        
        # Check if other server are using the same configuration file
        srvMatch = query_db('select rowid from servers where fileconfig=?', [fullpath_fileconfig], one=True)
        if srvMatch:
            return jsonify({'error':True, 
                            'errormsg':u"Can't exits two servers with the same configuration file.<br/>Please change configuration file name and try again."})
                    
        cfgbasic = twp.get_data_config_basics(fullpath_fileconfig)
        
        # Check if the port are be using by other server with the same gametype
        fport = int(cfgbasic['port'])
        while True:
            srvMatch = query_db('select rowid from servers where base_folder=? and port=?', [mod_folder, str(fport)], one=True)
            if not srvMatch:
                break
            fport += 1
        # Try write the new port in the configuration file
        # TODO: Create a method for write configuration files
        if not fport == int(cfgbasic['port']):
            if cfgbasic['empty']:
                try:
                    f = open(fullpath_fileconfig, "w")
                    srvcfg = f.write("sv_port %d\n" % fport);
                    f.close();
                except IOError:
                    return jsonify({'error':True, 'errormsg':str(e)})
            else:
                return jsonify({'error':True, 
                                'errormsg':u"Can't exits two servers with the same 'Port' in the same MOD.<br/>Please check or change configuration file and try again."})
        
        # If all checks good, create the new instance
        g.db.execute("INSERT INTO servers (fileconfig, base_folder, bin, port, name, gametype, register) VALUES (?,?,?,?,?,?)", \
                     [fullpath_fileconfig, mod_folder, bin, str(fport), cfgbasic['name'], cfgbasic['gametype'], cfgbasic['register']])
        g.db.commit()
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@app.route('/_remove_server_instance/<int:id>')
def remove_server_instance(id):
    if 'logged_in' in session and session['logged_in']:
        g.db.execute("DELETE FROM servers WHERE rowid=?", [id])
        g.db.execute("DELETE FROM issues WHERE server_id=?", [id])
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
            
            srvMatch = query_db('select rowid from servers where base_folder=? and port=? and rowid<>?', \
                                [srv['base_folder'], cfgbasic['port'], srvid], one=True)
            if srvMatch:
                return jsonify({'error':True, 
                                'errormsg':u"Can't exits two servers with the same 'Port' in the same MOD.<br/>Please check configuration and try again."})
            
            g.db.execute("UPDATE servers SET alaunch=?,port=?,name=?,gametype=?,register=? WHERE rowid=?", \
                         [alaunch, cfgbasic['port'], cfgbasic['name'], cfgbasic['gametype'], cfgbasic['register'], srvid])
            g.db.commit()
            try:
                cfgfile = open(srv['fileconfig'], "w")
                cfgfile.write(srvcfg)
                cfgfile.close()
            except IOError as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            return jsonify({'success':True, 'name':cfgbasic['name'], 'port':cfgbasic['port'], \
                            'gametype':cfgbasic['gametype'], 'register':cfgbasic['register'], 'id':srvid})
        return jsonify({'error':True, 'errormsg':u'Operation Invalid: Server not exists!'})
    return jsonify({'notauth':True})

@app.route('/_get_server_config/<int:id>')
def get_server_config(id):
    if 'logged_in' in session and session['logged_in']:
        srv = query_db('select alaunch,fileconfig,base_folder from servers where rowid=?', [id], one=True)
        if srv:
            (rest, filename) = srv['fileconfig'].rsplit('/', 1)
            (filename, rest) = filename.split('.', 1)
            if os.path.exists(srv['fileconfig']):
                try:
                    cfgfile = open(srv['fileconfig'], "r")
                    srvcfg = cfgfile.read()
                    cfgfile.close()
                except IOError as e:
                    srvcfg = str(e)
            else:
                srvcfg = ""
            return jsonify({'success':True, 'alsrv':srv['alaunch'], 'srvcfg':srvcfg, 'fileconfig':filename})
        return jsonify({'error':True, 'errormsg':u'Operation Invalid: Server not exists!'})
    return jsonify({'notauth':True})

@app.route('/_get_mod_configs/<string:mod_folder>')
def get_mod_configs(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        jsoncfgs = {'configs':[]}
        cfgs = twp.get_mod_configs(SERVERS_BASEPATH, mod_folder)
        for config in cfgs:
            srv = query_db('select rowid from servers where fileconfig=?', ['%s/%s/%s' % (SERVERS_BASEPATH, mod_folder, config)], one=True)
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
                return jsonify({'error':True, 'errormsg':u'Undefined server binary file!'})
            
            srvMatch = query_db("select rowid from servers WHERE status='Running' and port=?", [srv['port']], one=True)
            if srvMatch:
                return jsonify({'error':True, 'errormsg':u'Can\'t run two servers in the same port!'})
            
            subprocess.Popen(['%s/%s/%s' % (SERVERS_BASEPATH,srv['base_folder'],srv['bin']), \
                              '-f', srv['fileconfig']], \
                              shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1) # Be nice with the server...
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':u'Operation Invalid: Server not exists!'})
    return jsonify({'notauth':True})

@app.route('/_stop_server_instance/<int:id>')
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
                        return jsonify({'error':True, 'errormsg':'System failure: %s' % str(e)})
                    else:
                        return jsonify({'success':True})
                    break
            return jsonify({'error':True, 'errormsg':u'Operation Invalid: Can\'t found server pid'})
        else:
            return jsonify({'error':True, 'errormsg':u'Operation Invalid: Server not found'})
    return jsonify({'notauth':True})

@app.route('/_get_server_instances_online')
def get_server_instances_online():
    servers = query_db("SELECT rowid FROM servers WHERE status='Running'")
    return jsonify({'success':True, 'num':len(servers)})

@app.route('/_reboot')
def reboot():
    if 'logged_in' in session and session['logged_in']:
        shutdown_all_server_instances()
        
        try:
            subprocess.check_call("/sbin/shutdown -r now 'Reboot called by TWP'", shell=True)
        except:
            return jsonify({ 'error':True, 'errormsg':u"Can't reboot system!<br/><span class='text-muted'>need root privileges</span>"})
        return jsonify({'success':True })
    return jsonify({'notauth':True})


# Security Checks
def check_session_limit():
    if 'logged_in' in session and session.get('last_activity') is not None:
        now = int(time.time())
        limit = now - 60 * config.getint('session', 'time')
        last_activity = session.get('last_activity')
        if last_activity < limit:
            flash(u'Session timed out!', 'info')
            logout()
        else:
            session['last_activity'] = now
            

# Context Processors
@app.context_processor
def utility_processor():
    def get_mod_instances(mod_folder):
        servers = query_db('select rowid,* from servers where base_folder=?', [mod_folder])
        return servers
    def get_server_basics(id):
        srv = query_db('select port, name, gametype from servers where rowid=?', [id], one=True)
        if srv:
            return {'port':srv['port'], 'name':srv['name'], 'gametype':srv['gametype']}
    def get_mod_binaries(mod_folder):
        return twp.get_mod_binaries(SERVERS_BASEPATH, mod_folder)
    return dict(get_mod_instances=get_mod_instances, 
                get_mod_binaries=get_mod_binaries, 
                get_server_basics=get_server_basics)


# Jobs
def check_servers_status():
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

def relaunch_servers_offline():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    
    # By default all players are offline
    g.db.execute("UPDATE players SET status=0")
    # By default all servers are offline
    g.db.execute("UPDATE servers SET status='Stopped'")
    
    servers = query_db('select rowid,* from servers')
    net_servers_info = twp.get_server_net_info("127.0.0.1", servers)
    online_ids = []
    # Check Teeworlds Requests
    for server in net_servers_info:
        # It's online because have a 'gametype'
        if not server['netinfo'].gametype == None:
            rows = query_db("UPDATE servers set status='Running' where rowid=? and lower(gametype)=?", [server['srvid'], server['netinfo'].gametype.lower()], one=True)
            if rows:
                online_ids.append(server['srvid'])
                # Update or create players seen
                for player in server['netinfo'].playerlist:
                    playerMatch = query_db('select * from players where lower(name)=?', [player.name.lower()], one=True)
                    if not playerMatch:
                        g.db.execute("INSERT INTO players (name,create_date,last_seen_date,status) VALUES (?,?,?,1)", \
                                     [player.name, str(time.strftime('%m/%d/%Y %H:%M')), str(time.strftime('%m/%d/%Y %H:%M'))])
                    else:
                        g.db.execute("UPDATE players SET last_seen_date=?, status=1 WHERE lower(name)=?", \
                                     [str(time.strftime('%m/%d/%Y %H:%M')), player.name.lower()])
                
    # Trye reopen server
    for server in servers:
        if server['rowid'] not in online_ids:
            if server['alaunch'] == 1 and not server['bin'] == None:
                # Report issue
                g.db.execute("INSERT INTO issues (server_id, date) VALUES (?,?)", [server['rowid'], str(time.strftime('%m/%d/%Y %H:%M:%S'))])
                # Open server
                subprocess.Popen(['%s/%s/%s' % (SERVERS_BASEPATH,server['base_folder'],server['bin']), \
                                  '-f', server['fileconfig']], \
                                  shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)     
    
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
    for connn in netstat:
        servers = query_db("SELECT base_folder,bin FROM servers WHERE port=?", [conn[0]])
        for srv in servers:
            if conn[2].endswith('%s/%s' % (server['base_folder'],server['bin'])):
                os.kill(int(conn[1]), signal.SIGTERM)
    

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
