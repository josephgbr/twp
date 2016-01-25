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
import twpl
import subprocess, time, re, hashlib, os, sys, json, logging, time, \
        signal, shutil
from mergedict import ConfigDict
from io import BytesIO
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, \
                  flash, jsonify, send_from_directory, send_file
from sqlalchemy import or_, func, desc
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask.ext.babel import Babel, _
from twpl import BannedList, BannerGenerator, TWPConfig
import logging
logging.basicConfig() 
    

# Start Flask App
app = Flask(__name__)
app.config.from_object(TWPConfig())
babel = Babel(app)
db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Global
BANLIST = BannedList()
PUBLIC_IP = twpl.get_public_ip()

# Check Servers path
app.config['SERVERS_BASEPATH'] = r'%s/%s' % (app.root_path, 
                                             app.config['SERVERS_BASEPATH']) if not app.config['SERVERS_BASEPATH'][0] == '/' else app.config['SERVERS_BASEPATH']
if not os.path.isdir(app.config['SERVERS_BASEPATH']):
    os.makedirs(app.config['SERVERS_BASEPATH'])
    
# Create Tables
class Issue(db.Model):
    __tablename__ = 'issue'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    message = db.Column(db.String(512))
    
class PlayerServerInstance(db.Model):
    __tablename__ = 'player_server_instance'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    name = db.Column(db.String(25), nullable=False)
    clan = db.Column(db.String(25))
    country = db.Column(db.Integer)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    
class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=func.now())
    last_seen_date = db.Column(db.DateTime, nullable=False, default=func.now())
    status = db.Column(db.Integer, nullable=False)
    
class ServerInstance(db.Model):
    __tablename__ = 'server_instance'
    id = db.Column(db.Integer, primary_key=True)
    fileconfig = db.Column(db.String(128), nullable=False)
    base_folder = db.Column(db.String(512), nullable=False)
    bin = db.Column(db.String(128))
    alaunch = db.Column(db.Boolean, default=False)
    port = db.Column(db.String(4), default='8303')
    name = db.Column(db.String(128), default="Unnamed Server")
    status = db.Column(db.Integer, default=0)
    gametype = db.Column(db.String(16), default='DM')
    visible = db.Column(db.Boolean, default=True)
    public = db.Column(db.Boolean, default=True)
    logfile = db.Column(db.String(128))
    econ_port = db.Column(db.String(4))
    econ_password = db.Column(db.String(32))
    
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
class ServerJob(db.Model):
    __tablename__ = 'server_job'
    id = db.Column(db.String(191), primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable = False)
    job_type = db.Column(db.Integer, nullable = False)
    job_exec = db.Column(db.String(4092))

db.create_all()


# DB Methods
def db_add_and_commit(reg):
    db.session.add(reg)
    db.session.commit()
    
def db_delete_and_commit(reg):
    db.session.delete(reg)
    db.session.commit()

def db_init():
    users_count = User.query.count()
    if users_count == 0:
        user = User(username='admin', password=str_sha512_hex_encode('admin'))
        db_add_and_commit(user)


# App Callbacks
@app.before_request
def before_request():
    BANLIST.refresh()
    if not request.path.startswith('/banned') and BANLIST.find(request.remote_addr):
        return redirect(url_for('banned'))
    
    if request.view_args and 'lang_code' in request.view_args:
        g.current_lang = request.view_args['lang_code']
        request.view_args.pop('lang_code')
        
    check_session()

#@app.teardown_request
#def teardown_request(exception):

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['SUPPORT_LANGUAGES'])

#@babel.timezoneselector
#def get_timezone():


# Routing
@app.route("/", methods=['GET'])
@app.route("/overview", methods=['GET'])
def overview():
    session['prev_url'] = request.path;
    return render_template('index.html', dist=twpl.get_linux_distribution(), ip=PUBLIC_IP)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not BANLIST.find(request.remote_addr) and get_login_tries() >= app.config['LOGIN_MAX_TRIES']:
        BANLIST.add(request.remote_addr, app.config['LOGIN_BAN_TIME']);
        session['login_try'] = 0;
        return redirect(url_for("banned")) 
    
    if request.method == 'POST':
        request_username = request.form['username']
        request_passwd = str_sha512_hex_encode(request.form['password'])

        current_url = session['prev_url'] if 'prev_url' in session else url_for('overview')

        dbuser = db.session.query(User).filter(User.username == request_username, User.password == request_passwd)
        if dbuser.count() > 0:
            dbuser = dbuser.one()
            session['logged_in'] = True
            session['last_activity'] = int(time.time())
            session['username'] = dbuser.username
            flash(_('You are logged in!'), 'success')

            if current_url == url_for('login'):
                return redirect(url_for('overview'))
            return redirect(current_url)

        session['login_try'] = get_login_tries()+1
        session['last_login_try'] = int(time.time())
        flash(_('Invalid username or password! ({0}/{1})').format(get_login_tries(),
                                                                  app.config['LOGIN_MAX_TRIES']), 'danger')
    return render_template('login.html')

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

@app.route('/banned', methods=['GET'])
def banned():
    return render_template('banned.html'), 403

@app.route('/servers', methods=['GET'])
def servers():
    session['prev_url'] = request.path;

    db.session.query(ServerInstance).update({ServerInstance.status:0})
    db.session.commit()

    netstat = twpl.netstat()
    for conn in netstat:
        if not conn[2]:
            continue
        (rest,base_folder,bin) = conn[2].rsplit('/', 2)
        srv = db.session.query(ServerInstance).filter(ServerInstance.port==conn[0], 
                                                      ServerInstance.base_folder==base_folder, 
                                                      ServerInstance.bin==bin)
        if srv.count() > 0:
            srv = srv.one()
            net_server_info = twpl.get_server_net_info("127.0.0.1", [srv])[0]
            # FIXME: Check info integrity
            if net_server_info and net_server_info['netinfo'].gametype:
                srv.status = 1
                srv.name = net_server_info['netinfo'].name
                srv.gametype = net_server_info['netinfo'].gametype
                db_add_and_commit(srv)
    return render_template('servers.html', servers=twpl.get_local_servers(app.config['SERVERS_BASEPATH']))
    
@app.route('/server/<int:id>', methods=['GET'])
def server(id):
    session['prev_url'] = request.path;
    srv = db.session.query(ServerInstance).get(id)

    netinfo = None
    if srv:
        netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
    else:
        flash(_('Server not found!'), "danger")
    return render_template('server.html', ip=PUBLIC_IP, server=srv, netinfo=netinfo)

@app.route('/server/<int:id>/banner', methods=['GET'])
def generate_server_banner(id):
    srv = db.session.query(ServerInstance).get(id)
    if srv:
        netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
        banner_image = BannerGenerator((600, 40), srv, netinfo)
        
        if 'title' in request.values:
            banner_image.titleColor = twpl.HTMLColorToRGBA(request.values.get('title'))
        if 'detail' in request.values:
            banner_image.detailColor = twpl.HTMLColorToRGBA(request.values.get('detail'))
        if 'address' in request.values:
            banner_image.addressColor = twpl.HTMLColorToRGBA(request.values.get('address'))
        if 'grads' in request.values:
            banner_image.gradStartColor = twpl.HTMLColorToRGBA(request.values.get('grads'))
        if 'grade' in request.values:
            banner_image.gradEndColor = twpl.HTMLColorToRGBA(request.values.get('grade'))
        
        return send_file(banner_image.generate(PUBLIC_IP), as_attachment=False)
        
@app.route('/players', methods=['GET'])
def players():
    session['prev_url'] = request.path;
    
    players = db.session.query(Player).order_by(desc(Player.last_seen_date)).order_by(desc(Player.name))
    return render_template('players.html', players=players)

@app.route('/maps', methods=['GET'])
def maps():
    session['prev_url'] = request.path;
    return redirect(url_for('overview'))

@app.route('/settings', methods=['GET','POST'])
def settings():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            flash(_('Settings updates successfully'), 'info')
        else:
            session['prev_url'] = request.path;
        return render_template('settings.html')
    else:
        flash(_('Can\'t access to settings page'), 'danger')
        return redirect(url_for('overview'))

@app.route('/install_mod', methods=['POST'])
def install_mod():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('servers')
    if 'logged_in' in session and session['logged_in']:
        if 'url' in request.form and not request.form['url'] == '':
            try:
                twpl.install_mod_from_url(request.form['url'], app.config['SERVERS_BASEPATH'])
            except Exception as e:
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
                        twpl.extract_targz(fullpath, app.config['SERVERS_BASEPATH'], True)
                    elif filename.endswith(".zip"):
                        twpl.extract_zip(fullpath, app.config['SERVERS_BASEPATH'], True)
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
    servers = list()
    players = list()
    searchword = request.args.get('r', '')

    sk = "%%%s%%" % searchword
    servers = db.session.query(ServerInstance).filter(or_(ServerInstance.name.like(sk), 
                                                          ServerInstance.base_folder.like(sk)))
    players = db.session.query(Player).filter(Player.name.like(sk))
    return render_template('search.html', search=searchword, servers=servers, players=players)

@app.route('/log/<int:id>/<string:code>/<string:name>', methods=['GET'])
def log(id, code, name):
    srv = db.session.query(ServerInstance).get(id)
    netinfo = None
    logdate = None
    if srv:
        log_file = r'%s/%s/logs/%s-%s' % (app.config['SERVERS_BASEPATH'], srv.base_folder, code, name)
        if not os.path.isfile(log_file):
            flash(_('Logfile not exists!'), "danger")
        else:
            dt = datetime.fromtimestamp(time.mktime(time.localtime(int(code, 16))))
            logdate = dt.strftime("%d-%m-%Y %H:%M:%S")
            netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
    else:
        flash(_('Server not found!'), "danger")
    return render_template('log.html', ip=PUBLIC_IP, server=srv, logcode=code, logname=name, logdate=logdate)
    

@app.route('/_upload_maps/<int:id>', methods=['POST'])
def upload_maps(id):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            download_folder = r'%s/%s/data/maps' % (app.config['SERVERS_BASEPATH'], srv.base_folder)
            app.logger.info(len(request.files))
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    fullpath = r'%s/%s' % (app.config['UPLOAD_FOLDER'], filename)
                    if filename.endswith(".tar.gz"):
                        twpl.extract_targz(fullpath, download_folder, True)
                    elif filename.endswith(".zip"):
                        twpl.extract_zip(fullpath, download_folder, True)
                    elif filename.endswith(".map"):
                        try:
                            fullpath_download = r'%s/%s' % (download_folder, filename)
                            if os.path.exists(fullpath_download):
                                os.remove(fullpath_download)
                            shutil.move(fullpath, fullpath_download)
                        except Exception as e:
                            return jsonify({'error':True, 'errormsg':str(e)})
                    return jsonify({'success':True})
                else:
                    return jsonify({'error':True, 'errormsg':_('Error: Can\'t upload selected maps')})
            else:
                return jsonify({'error':True, 'errormsg':_('Error: No file detected!')})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    else:
        return jsonify({'error':True, 'errormsg':_('Error: You haven\'t permissions for upload new maps!')})

@app.route('/_remove_map/<int:id>', methods=['POST'])
def remove_map(id):
    if 'logged_in' in session and session['logged_in']:
        if 'map' in request.form:
            map = request.form['map']
            srv = db.session.query(ServerInstance).get(id)
            if srv:
                fullpath = r'%s/%s/data/maps/%s.map' % (app.config['SERVERS_BASEPATH'],srv.base_folder,map)
                if os.path.isfile(fullpath):
                    os.unlink(fullpath)
                    return jsonify({'success':True})
                return jsonify({'error':True, 'errormsg':_('Error: Map not exists!')})
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Map not defined!')})
    return jsonify({'notauth':True})

@app.route('/_remove_mod', methods=['POST'])
def remove_mod():
    if 'logged_in' in session and session['logged_in']:
        if 'folder' in request.form:
            fullpath_folder = r'%s/%s' % (app.config['SERVERS_BASEPATH'], request.form['folder'])
            if os.path.exists(fullpath_folder):
                servers = db.session.query(ServerInstance).filter(ServerInstance.base_folder==request.form['folder'])
                for srv in servers:
                    stop_server(srv.id)
                    remove_server_instance(srv.id,1)
                shutil.rmtree(fullpath_folder)
                return jsonify({'success':True})
            else:
                return jsonify({'error':True, 'errormsg':_('Error: Folder mod not exists!')})
        else:
            return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})
    return jsonify({'notauth':True})

@app.route('/_refresh_cpu_host', methods=['POST'])
def refresh_cpu_host():
    if 'logged_in' in session and session['logged_in']:
        return twpl.host_cpu_percent()
    return jsonify({})

@app.route('/_refresh_uptime_host', methods=['POST'])
def refresh_uptime_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_uptime())
    return jsonify({})

@app.route('/_refresh_disk_host', methods=['POST'])
def refresh_disk_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_disk_usage(partition=app.config['PARTITION']))
    return jsonify({})

@app.route('/_refresh_memory_host', methods=['POST'])
def refresh_memory_containers():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_memory_usage())
    return jsonify({})

@app.route('/_refresh_host_localtime', methods=['POST'])
def refresh_host_localtime():
    return jsonify(twpl.host_localtime())

@app.route('/_get_all_online_servers', methods=['POST'])
def get_all_online_servers():
    return jsonify(twpl.get_tw_masterserver_list(PUBLIC_IP))

@app.route('/_create_server_instance/<string:mod_folder>', methods=['POST'])
def create_server_instance(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        fileconfig = request.form['fileconfig']
        if not fileconfig or fileconfig == "":
            return jsonify({'error':True, 'errormsg':_('Invalid configuration file name.')})
        
        fileconfig = '%s.conf' % fileconfig
        fullpath_fileconfig = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'],mod_folder,fileconfig)
        
        # Search for mod binaries, if only exists one use it
        bin = None
        srv_bins = twpl.get_mod_binaries(app.config['SERVERS_BASEPATH'], mod_folder)
        if srv_bins and len(srv_bins) == 1:
            bin = srv_bins[0]
        
        # Check if other server are using the same configuration file
        srvMatch = db.session.query(ServerInstance).filter(ServerInstance.fileconfig==fileconfig, 
                                                           ServerInstance.base_folder==mod_folder)
        if srvMatch.count() > 0:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exists two servers with the same configuration file.<br/>\
                            Please change configuration file name and try again.")})
                    
        cfgbasic = twpl.get_data_config_basics(fullpath_fileconfig)
        
        # Check if the logfile are be using by other server with the same base_folder
        if cfgbasic['logfile']:
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.logfile==cfgbasic['logfile'], 
                                                               ServerInstance.base_folder==mod_folder)
            if srvMatch.count() > 0:
                return jsonify({'error':True, 
                                'errormsg':_("Can't exits two servers with the same log file.<br/>\
                                Please check configuration and try again.")})
            
        # Check if the econ_port are be using by other server
        if cfgbasic['econ_port']:
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.econ_port==cfgbasic['econ_port'])
            if srvMatch.count() > 0:
                return jsonify({'error':True, 
                                'errormsg':_("Can't exits two servers with the same 'ec_port'.<br/>\
                                Please check configuration and try again.")})
        
        # Check if the port are be using by other server with the same base_folder
        fport = int(cfgbasic['port'])
        while True:
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.port==str(fport), 
                                                               ServerInstance.base_folder==mod_folder)
            if srvMatch.count() < 1:
                break
            fport += 1

        try:
            if cfgbasic['name'] == 'unnamed server':
                cfgbasic['name'] = "Server created with Teeworlds Web Panel"
                twpl.write_config_param(fullpath_fileconfig, "sv_name", cfgbasic['name'])
            if not fport == int(cfgbasic['port']):
                cfgbasic['port'] = str(fport)
                twpl.write_config_param(fullpath_fileconfig, "sv_port", cfgbasic['port'])
        except Exception, e:
             return jsonify({'error':True, 'errormsg':str(e)})
            
        # If all checks good, create the new instance
        nserver = ServerInstance(fileconfig=fileconfig,
                                 base_folder=mod_folder,
                                 bin=bin,
                                 port=str(fport),
                                 name=cfgbasic['name'],
                                 gametype=cfgbasic['gametype'],
                                 visible=True if cfgbasic['register'] and cfgbasic['register'] == 1 else False,
                                 public=False if cfgbasic['password'] else True,
                                 logfile=cfgbasic['logfile'],
                                 econ_port=cfgbasic['econ_port'],
                                 econ_password=cfgbasic['econ_pass'],
                                 status=0)
        db_add_and_commit(nserver)
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@app.route('/_remove_server_instance/<int:id>/<int:delconfig>', methods=['POST'])
def remove_server_instance(id, delconfig=0):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if not srv:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        
        if delconfig == 1:
            os.unlink(r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig))
        
        db_delete_and_commit(srv)
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@app.route('/_set_server_binary/<int:id>/<string:binfile>', methods=['POST'])
def set_server_binary(id, binfile):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        # Check that is a correct binary name (exists in mod folder)
        srv_bins = twpl.get_mod_binaries(app.config['SERVERS_BASEPATH'], srv.base_folder)
        if not srv_bins == None and binfile in srv_bins:
            srv.bin = binfile
            db_add_and_commit(srv)
            return jsonify({'success':True})
        return jsonify({'invalidBinary':True})
    return jsonify({'notauth':True})

@app.route('/_save_server_config', methods=['POST'])
def save_server_config():
    if 'logged_in' in session and session['logged_in']:
        srvid = int(request.form['srvid'])
        alaunch = 'alsrv' in request.form and request.form['alsrv'] == 'true'
        srvcfg = request.form['srvcfg'];
        srv = db.session.query(ServerInstance).get(srvid)
        if srv:
            cfgbasic = twpl.parse_data_config_basics(srvcfg)
            
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.base_folder==srv.base_folder, 
                                                               ServerInstance.port==cfgbasic['port'], 
                                                               ServerInstance.id!=srvid)
            if srvMatch.count() > 0:
                return jsonify({'error':True, \
                                'errormsg':_("Can't exits two servers with the same 'sv_port' in the same MOD.<br/>\
                                Please check configuration and try again.")})
                
            # Check if the logfile are be using by other server with the same base_folder
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.base_folder==srv.base_folder, 
                                                               ServerInstance.logfile==cfgbasic['logfile'], 
                                                               ServerInstance.id!=srvid)
            if srvMatch.count() > 0:
                return jsonify({'error':True, 
                                'errormsg':_("Can't exits two servers with the same log file.<br/>\
                                Please check configuration and try again.")})
            
            srv.alaunch = alaunch
            srv.port = cfgbasic['port']
            srv.name = cfgbasic['name']
            srv.gametype = cfgbasic['gametype']
            srv.visible = True if cfgbasic['register'] and cfgbasic['register'] == 1 else False
            srv.public = False if cfgbasic['password'] else True
            srv.logfile = cfgbasic['logfile']
            srv.econ_port = cfgbasic['econ_port']
            srv.econ_password = cfgbasic['econ_pass']
            db_add_and_commit(srv)
            
            try:
                cfgfile = open(r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig), "w")
                cfgfile.write(srvcfg)
                cfgfile.close()
            except IOError as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            res = {'success':True, 'cfg':cfgbasic, 'id':srvid}
            res.update(cfgbasic)
            return jsonify(res)
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_config/<int:id>', methods=['POST'])
def get_server_config(id):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            ## Config File Text
            fullpath_fileconfig = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig)
            (filename, rest) = srv.fileconfig.split('.', 1)
            if os.path.exists(fullpath_fileconfig):
                try:
                    cfgfile = open(fullpath_fileconfig, "r")
                    srvcfg = cfgfile.read()
                    cfgfile.close()
                except IOError as e:
                    srvcfg = str(e)
            else:
                srvcfg = ""
            
            return jsonify({'success':True, 'alsrv':srv.alaunch, 'srvcfg':srvcfg, 'fileconfig':filename})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_issues/<int:id>', methods=['POST'])
@app.route('/_get_server_issues/<int:id>/<int:page>', methods=['POST'])
def get_server_issues(id, page=0):
    if 'logged_in' in session and session['logged_in']:
        RPP = 10
        dbissues = db.session.query(Issue).filter(Issue.server_id==id).order_by(desc(Issue.date))
        numpages = int(dbissues.count()/RPP)
        dbissues_page = dbissues.offset(RPP*page).limit(RPP)
        issues = [(dbissue.date, dbissue.message) for dbissue in dbissues_page]
        return jsonify({'success':True, 'issues':issues, 'pages':numpages})
    return jsonify({'notauth':True})

@app.route('/_get_server_issues_count/<int:id>', methods=['POST'])
def get_server_issues_count(id):
    if 'logged_in' in session and session['logged_in']:
        issues_count = db.session.query(Issue).filter(Issue.server_id==id).count()
        return jsonify({'success':True, 'issues_count':issues_count})
    return jsonify({})

@app.route('/_get_server_maps/<int:id>', methods=['POST'])
def get_server_maps(id):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if srv:            
            ## Maps
            maps = twpl.get_mod_maps(app.config['SERVERS_BASEPATH'], srv.base_folder)
            return jsonify({'success':True, 'maps':maps})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_get_mod_configs/<string:mod_folder>', methods=['POST'])
def get_mod_configs(mod_folder):
    if 'logged_in' in session and session['logged_in']:
        jsoncfgs = {'configs':[]}
        cfgs = twpl.get_mod_configs(app.config['SERVERS_BASEPATH'], mod_folder)
        for config in cfgs:
            srv = db.session.query(ServerInstance).filter(ServerInstance.fileconfig==config,
                                                          ServerInstance.base_folder==mod_folder)
            if srv.count() < 1:
                jsoncfgs['configs'].append(os.path.splitext(config)[0])
        return jsonify(jsoncfgs)
    return jsonify({'notauth':True})

@app.route('/_get_mod_wizard_config/<int:id>', methods=['POST'])
def get_mod_wizard_config(id):
    if 'logged_in' in session and session['logged_in']:        
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            fullpath = r'%s/%s/config.json' % (app.config['SERVERS_BASEPATH'],srv.base_folder)
            if os.path.isfile(fullpath):
                cfgfile = open(fullpath, "r")
                config = cfgfile.read()
                cfgfile.close()
                return jsonify({'success':True, 'config':config})
            return jsonify({'success':True}) # Not exists, no problem
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_start_server_instance/<int:id>', methods=['POST'])
def start_server(id):
    if 'logged_in' in session and session['logged_in']:        
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            if not srv.bin:
                return jsonify({'error':True, 'errormsg':_('Undefined server binary file!!')})
            
            srvMatch = db.session.query(ServerInstance).filter(ServerInstance.status==1,
                                                    ServerInstance.port==srv.port)
            if srvMatch.count() > 0:
                return jsonify({'error':True, 'errormsg':_('Can\'t run two servers in the same port!')})
            
            try:
                start_server_instance(srv.base_folder, srv.bin, srv.fileconfig)
            except Exception as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            
            time.sleep(1) # Be nice with the server...
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@app.route('/_stop_server_instance/<int:id>', methods=['POST'])
def stop_server(id):
    if 'logged_in' in session and session['logged_in']:
        dbserver = db.session.query(ServerInstance).get(id)
        if dbserver:
            binpath = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'], dbserver.base_folder, dbserver.bin)
            proc = twpl.search_server_pid(binpath, dbserver.fileconfig)
            if proc:
                os.kill(proc, signal.SIGTERM)
                return jsonify({'success':True})
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Can\'t found server pid')})
        else:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_instances_online', methods=['POST'])
def get_server_instances_online():
    servers = db.session.query(ServerInstance).filter(ServerInstance.status==1)
    return jsonify({'success':True, 'num':servers.count()})

@app.route('/_get_server_instance_log/<int:id>/<int:seek>', methods=['POST'])
def get_current_server_instance_log(id, seek):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            logcontent = ""
            if not srv.logfile:
                return jsonify({'error':True, 'errormsg':_('Logfile not defined!')})
            try:
                if srv.logfile[0] == '/':
                    fullpath = srv.logfile
                else:
                    fullpath = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'],srv.base_folder,srv.logfile)
                
                file_size = os.path.getsize(fullpath)
                if seek >= file_size:
                    return jsonify({'success':True, 'content':None, 'seek':file_size})
                
                cfgfile = open(fullpath, "r")
                cfgfile.seek(seek)
                logcontent = cfgfile.read()
                logseek = cfgfile.tell()
                cfgfile.close()
            except Exception as e:
                return jsonify({'success':True, 'content':None, 'seek':0})
            
            lines = logcontent.splitlines()
            logcontent = list()
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
                    logcontent.append({'date':dt.strftime("%d-%m-%Y %H:%M:%S"),
                                       'section':section,
                                       'message':message,
                                       'type':type})
            
            return jsonify({'success':True, 'content':logcontent, 'seek':logseek})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@app.route('/_get_server_instance_log/<int:id>/<string:code>/<string:name>', methods=['POST'])
def get_selected_server_instance_log(id, code, name):
    if 'logged_in' in session and session['logged_in']:
        srv = db.session.query(ServerInstance).get(id)
        if srv:
            logcontent = ""
            log_file = r'%s/%s/logs/%s-%s' % (app.config['SERVERS_BASEPATH'], srv.base_folder, code, name)
            if not os.path.isfile(log_file):
                return jsonify({'error':True, 'errormsg':_('Logfile not exists!')})
            try:                                
                cfgfile = open(log_file, "r")
                logcontent = cfgfile.read()
                cfgfile.close()
            except Exception as e:
                return jsonify({'success':True, 'content':None})
            
            lines = logcontent.splitlines()
            logcontent = list()
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
                    logcontent.append({'date':dt.strftime("%d-%m-%Y %H:%M:%S"),
                                       'section':section,
                                       'message':message,
                                       'type':type})
            
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
        srv = db.session.query(ServerInstance).get(srvid)
        if srv and srv.econ_port and srv.econ_password:
            econ_cmd = request.form['cmd']
            rcv = ''
            try:
                rcv = twpl.send_econ_command(int(srv.econ_port), srv.econ_password, econ_cmd)
            except Exception as e:
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
        
        srv = db.session.query(ServerInstance).get(id)
        if srv and srv.econ_port and srv.econ_password:
            nick = request.form['nick']
            action = 'ban' if request.path.startswith('/_ban_player/') else 'kick' 
            try:
                if not twpl.send_econ_user_action(int(srv.econ_port), srv.econ_password, nick, action):
                    return jsonify({'error':True, 'errormsg':_('Can\'t found \'{0}\' player!').format(nick)})         
            except Exception as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found or econ not configured!')})
    return jsonify({'notauth':True})    

@app.route('/_get_chart_values/<string:chart>', methods=['POST'])
@app.route('/_get_chart_values/<string:chart>/<int:id>', methods=['POST'])
def get_chart_values(chart, id=None):
    today = datetime.now()
    allowed_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, 7)]
    labels = dict()
    values = dict()
    
    if chart.lower() == 'server':
        labels['players7d'] = list()
        values['players7d'] = list()
        # TODO: Filter only from today-7 to today...
        players = db.session.query(PlayerServerInstance).filter(PlayerServerInstance.server_id==id)
        if not players:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        chart_data = ConfigDict()
        for dbplayer in players:
            strdate = dbplayer.date.strftime("%Y-%m-%d")
            if not strdate in allowed_dates:
                continue
            if not strdate in chart_data.keys() or not dbplayer.name in chart_data[strdate]:
                chart_data.merge({strdate:[dbplayer.name]})
        for secc in allowed_dates:
            labels['players7d'].append(secc)
            values['players7d'].append(len(chart_data[secc]) if secc in chart_data else 0)
        
        query_data = db.session.execute("SELECT count(clan) as num, clan FROM \
                                        (SELECT DISTINCT name,clan,server_id FROM player_server_instance \
                                        WHERE clan IS NOT NULL) as tbl WHERE tbl.server_id=:id GROUP BY clan \
                                        ORDER BY num DESC LIMIT 5", {"id":id})
        if query_data:
            labels['topclan'] = list()
            values['topclan'] = list()
            for value in query_data:
                labels['topclan'].append(value.clan)
                values['topclan'].append(value.num)
                
        query_data = db.session.execute("SELECT count(country) as num, country FROM \
                                        (SELECT DISTINCT name,country,server_id FROM player_server_instance \
                                        WHERE clan IS NOT NULL) as tbl WHERE tbl.server_id=:id GROUP BY country \
                                        ORDER BY num DESC LIMIT 5", {"id":id})
        if query_data:
            labels['topcountry'] = list()
            values['topcountry'] = list()
            for value in query_data:
                labels['topcountry'].append(value.country)
                values['topcountry'].append(value.num)
            
        return jsonify({'success':True, 'values':values, 'labels':labels})
    elif chart.lower() == 'machine':
        labels['players7d'] = list()
        values['players7d'] = list()
        players = db.session.query(PlayerServerInstance)
        if not players:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        chart_data = ConfigDict()
        for dbplayer in players:
            strdate = dbplayer.date.strftime("%Y-%m-%d")
            if not strdate in allowed_dates:
                continue
            if not strdate in chart_data.keys() or not dbplayer.name in chart_data[strdate]:
                chart_data.merge({strdate:[dbplayer.name]})
        for secc in allowed_dates:
            labels['players7d'].append(secc)
            values['players7d'].append(len(chart_data[secc]) if secc in chart_data else 0)
        return jsonify({'success':True, 'values':values, 'labels':labels})
    return jsonify({'error':True, 'errormsg':_('Undefined Chart!')})

@app.route('/_set_user_password/<int:id>', methods=['POST'])
def set_user_password(id):
    if 'logged_in' in session and session['logged_in']:
        if 'pass_new' in request.form and 'pass_old' in request.form:
            dbuser = db.session.query(User).filter(User.id==id, 
                                                   User.password==str_sha512_hex_encode(str(request.form['pass_old']))).one()
            if dbuser:
                dbuser.password = str(request.form['pass_new'])
                db_add_and_commit(dbuser)
                return jsonify({'success':True})
            return jsonify({'error':True, 'errormsg':_('Error: Can\'t change admin password. \
                                                        Check settings and try again.')})
        else:
            return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})
    return jsonify({'notauth':True})


# Security Checks
def check_session():
    if 'logged_in' in session and session.get('last_activity') is not None:
        now = int(time.time())
        limit = now - 60 * app.config['SESSION_TIME']
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
        servers = db.session.query(ServerInstance).filter(ServerInstance.base_folder==mod_folder)
        return servers
    def get_mod_binaries(mod_folder):
        return twpl.get_mod_binaries(app.config['SERVERS_BASEPATH'], mod_folder)
    return dict(get_mod_instances=get_mod_instances, 
                get_mod_binaries=get_mod_binaries)


# Jobs
def analyze_all_server_instances():
    db.session.query(Player).update({Player.status:0})
    db.session.query(ServerInstance).update({ServerInstance.status:0})
    
    # Check Server & Player Status
    netstat = twpl.netstat()
    for conn in netstat:
        if not conn[2]:
            continue
        objMatch = re.match("^.+\/([^\/]+)\/(.+)$", conn[2])
        if objMatch:
            (base_folder,bin) = [objMatch.group(1), objMatch.group(2)]
            srv = db.session.query(ServerInstance).filter(ServerInstance.port==conn[0],
                                                    ServerInstance.base_folder==base_folder,
                                                    ServerInstance.bin==bin)
            if srv.count() > 0:
                srv = srv.one()
                srv.status = 1
                netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
                for ntplayer in netinfo.playerlist:
                    nplayer = PlayerServerInstance(server_id = srv.id,
                                     name = ntplayer.name,
                                     clan = ntplayer.clan,
                                     country = ntplayer.country,
                                     date = func.now())
                    db.session.add(nplayer)
                    
                    playersMatch = db.session.query(Player).filter(func.lower(Player.name)==ntplayer.name.lower())
                    if playersMatch.count() < 1:
                        nplayer = Player(name=ntplayer.name,
                                         status=1)
                        db.session.add(nplayer)
                    else:
                        playerMatch = playersMatch.one()
                        playerMatch.last_seen_date = func.now()
                        playerMatch.status = 1
                        db.session.add(playerMatch)
                    
    # Reopen Offline Servers
    servers = db.session.query(ServerInstance).filter(ServerInstance.status==0, ServerInstance.alaunch==True)
    for dbserver in servers:            
        if not os.path.isfile(r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'], dbserver.base_folder, dbserver.bin)):
            nissue = Issue(server_id=dbserver.id,
                           message=_('Server binary not found'))
            db.session.add(nissue)
            continue
        
        if dbserver.logfile:
            current_time_hex = hex(int(time.time())).split('x')[1]
            logs_folder = r'%s/%s/logs' % (app.config['SERVERS_BASEPATH'], dbserver.base_folder)
            log_file = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'], dbserver.base_folder, dbserver.logfile)
            # Create logs folder if not exists
            if not os.path.isdir(logs_folder):
                os.makedirs(logs_folder)
            # Move current log to logs folder
            if os.path.isfile(log_file):
                shutil.move(log_file, r'%s/%s-%s' % (logs_folder, current_time_hex, dbserver.logfile))
            nissue = Issue(server_id=dbserver.id,
                           message="%s <a class='btn btn-xs btn-primary pull-right' href='/log/%d/%s/%s'>View log</a>" % (_('Server Offline'), 
                                                                                                                          dbserver.id, 
                                                                                                                          current_time_hex, 
                                                                                                                          dbserver.logfile))
        else:
            nissue = Issue(server_id=dbserver.id,
                           message=_('Server Offline'))
        db.session.add(nissue)
        # Open server
        start_server_instance(dbserver.base_folder, dbserver.bin, dbserver.fileconfig) 
    
    db.session.commit()
scheduler.add_job('analyze_all_server_instances', analyze_all_server_instances, 
                  trigger={'second':30, 'type':'cron'}, replace_existing=True)
        

# Tools
def str_sha512_hex_encode(strIn):
    return hashlib.sha512(strIn.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
           
def shutdown_all_server_instances():
    netstat = twpl.netstat()
    for conn in netstat:
        servers = query_db("SELECT base_folder,bin FROM servers WHERE port=?", [conn[0]])
        for srv in servers:
            if conn[2].endswith('%s/%s' % (server['base_folder'],server['bin'])):
                os.kill(int(conn[1]), signal.SIGTERM)

def start_server_instance(base_folder, bin, fileconfig):
    binpath = r'%s/%s/%s' % (app.config['SERVERS_BASEPATH'], base_folder, bin)
    # Force it! (prevent zombie state)
    proc = twpl.search_server_pid(binpath, fileconfig)
    if proc:
        os.kill(proc, signal.SIGKILL)
    
    subprocess.Popen([binpath, '-f', fileconfig],
                    shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=r'%s/%s' % (app.config['SERVERS_BASEPATH'], base_folder),
                    close_fds=True,
                    preexec_fn=os.setsid)

def get_login_tries():
    return int(session.get('login_try')) if 'login_try' in session else 0


# Init Module
if __name__ == "__main__":
    db_init()
    if len(app.config['LOGFILE']) > 0:
        handler = RotatingFileHandler(app.config['LOGFILE'], maxBytes=app.config['LOGBYTES'], backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    if app.config['SSL']: 
        from OpenSSL import SSL
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(app.config['PKEY'])
        context.use_certificate_file(app.config['CERT'])
        app.run(host=app.config['HOST'], port=app.config['PORT'], 
                threaded=app.config['THREADED'], ssl_context=context)
    else:
        app.run(host=app.config['HOST'], port=app.config['PORT'], threaded=app.config['THREADED'])
        
    #shutdown_all_server_instances()
