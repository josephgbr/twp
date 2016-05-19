# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.3.0 - Teeworlds Web Panel
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
from twp import twp, SUPERUSER_ID, check_session, get_session_user,\
                get_session_server_permission_level, allowed_file, start_server_instance
import re, os, time, signal, shutil
from datetime import datetime
from io import open
from flask import request, session, redirect, url_for, render_template, \
                  flash, jsonify, current_app
from flask.ext.babel import Babel, _, format_datetime
from sqlalchemy import func, desc, asc
from werkzeug import secure_filename
from twpl.models import *

#################################
# GET
#################################
@twp.route('/settings', methods=['GET'])
@check_session(level='user')
def settings():
    session['prev_url'] = request.path;
    
    users = User.query.filter(User.token == None).order_by(asc(User.id)).all()
    users_token = User.query.filter(User.token != None).order_by(asc(User.id)).all()
    permission_levels = PermissionLevel.query.order_by(asc(PermissionLevel.id)).all()
    servers = ServerInstance.query
    return render_template('pages/settings.html', users=users, servers=servers,
                           users_token=users_token, 
                           permission_levels=permission_levels)
    
@twp.route('/log/<int:srvid>/<string:code>/<string:name>', methods=['GET'])
@check_session(level='user')
def log(srvid, code, name):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.log:
        srv = ServerInstance.query.get(srvid)
        netinfo = None
        logdate = None
        if srv:
            log_file = r'%s/%s/logs/%s-%s' % (current_app.config['SERVERS_BASEPATH'], srv.base_folder, code, name)
            if not os.path.isfile(log_file):
                flash(_('Logfile not exists!'), "danger")
            else:
                dt = datetime.fromtimestamp(time.mktime(time.localtime(int(code, 16))))
                logdate = format_datetime(dt)
                netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
        else:
            flash(_('Server not found!'), "danger")
        return render_template('pages/log.html', ip=PUBLIC_IP, server=srv, logcode=code, logname=name, logdate=logdate)
    return redirect(url_for('twp.overview'))


#################################
# POST
#################################
@twp.route('/_set_user_password', methods=['POST'])
@check_session(level='user')
def set_user_password():    
    if 'pass_new' in request.form and 'pass_old' in request.form:
        dbuser = User.query.filter(User.id==session['uid'], 
                                    User.password==twpl.str_sha512_hex_encode(str(request.form['pass_old']))).one()
        if dbuser:
            dbuser.password = str(request.form['pass_new'])
            db_add_and_commit(dbuser)
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Error: Can\'t change password. '+\
                                                   'Check settings and try again.')})
    else:
        return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})
    
@twp.route('/_upload_maps/<int:srvid>', methods=['POST'])
@check_session(level='user')
def upload_maps(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:
        srv = ServerInstance.query.get(srvid)
        if srv:
            download_folder = r'%s/%s/data/maps' % (current_app.config['SERVERS_BASEPATH'], srv.base_folder)
            if not os.path.isdir(download_folder):
                os.makedirs(download_folder)

            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    fullpath = r'%s/%s' % (current_app.config['UPLOAD_FOLDER'], filename)
                    if filename.lower().endswith(".map"):
                        try:
                            fullpath_download = r'%s/%s' % (download_folder, filename)
                            if os.path.exists(fullpath_download):
                                os.remove(fullpath_download)
                            shutil.move(fullpath, fullpath_download)
                        except Exception as e:
                            return jsonify({'error':True, 'errormsg':str(e)})
                    elif not twpl.extract_maps_package(fullpath, download_folder, True):
                        return jsonify({'error':True, 'errormsg':_('Invalid map package')})
                    db_create_server_staff_registry(srv.id, "Uploaded new maps ({0})".format(filename))
                    return jsonify({'success':True})
                else:
                    return jsonify({'error':True, 'errormsg':_('Error: Can\'t upload selected maps')})
            else:
                return jsonify({'error':True, 'errormsg':_('Error: No file detected!')})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    else:
        return jsonify({'error':True, 'errormsg':_('Error: You haven\'t permissions for upload new maps!')})

@twp.route('/_remove_map/<int:srvid>', methods=['POST'])
@check_session(level='user')
def remove_map(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:
        if 'map' in request.form:
            map = request.form['map']
            srv = ServerInstance.query.get(srvid)
            if srv:
                fullpath = r'%s/%s/data/maps/%s.map' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder,map)
                if os.path.isfile(fullpath):
                    os.unlink(fullpath)
                    db_create_server_staff_registry(srv.id, "Removed the map '{0}'".format(map))
                    return jsonify({'success':True})
                return jsonify({'error':True, 'errormsg':_('Error: Map not exists!')})
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Map not defined!')})
    return jsonify({'notauth':True})

@twp.route('/_set_server_binary/<int:srvid>/<string:binfile>', methods=['POST'])
@check_session(level='user')
def set_server_binary(srvid, binfile):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.start:
        srv = ServerInstance.query.get(srvid)
        # Check that is a correct binary name (exists in mod folder)
        srv_bins = twpl.get_mod_binaries(current_app.config['SERVERS_BASEPATH'], srv.base_folder)
        if not srv_bins == None and binfile in srv_bins:
            srv.bin = binfile
            db_add_and_commit(srv)
            return jsonify({'success':True})
        return jsonify({'invalidBinary':True})
    return jsonify({'notauth':True})

@twp.route('/_save_server_config/<int:srvid>', methods=['POST'])
@check_session(level='user')
def save_server_config(srvid):    
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:
        alaunch = 'alsrv' in request.form and request.form['alsrv'] == 'true'
        srvcfg = request.form['srvcfg'];
        srv = ServerInstance.query.get(srvid)
        if srv:
            cfgbasic = twpl.parse_data_config_basics(srvcfg)
            
            srvMatch = ServerInstance.query.filter(ServerInstance.base_folder.ilike(srv.base_folder), 
                                                    ServerInstance.port.ilike(cfgbasic['port']), 
                                                    ServerInstance.id!=srvid)
            if srvMatch.count() > 0:
                return jsonify({'error':True, \
                                'errormsg':_("Can't exist two servers with the same 'sv_port' in the same MOD.<br/>"+\
                                             "Please check configuration and try again.")})
                
            # Check if the logfile are be using by other server with the same base_folder
            if cfgbasic['logfile']:
                srvMatch = ServerInstance.query.filter(ServerInstance.base_folder.ilike(srv.base_folder), 
                                                        ServerInstance.logfile.ilike(cfgbasic['logfile']), 
                                                        ServerInstance.id!=srvid)
                if srvMatch.count() > 0:
                    return jsonify({'error':True, 
                                    'errormsg':_("Can't exist two servers with the same log file.<br/>"+\
                                                 "Please check configuration and try again.")})
            
            srv.alaunch = alaunch
            srv.port = cfgbasic['port']
            srv.name = cfgbasic['name']
            srv.gametype = cfgbasic['gametype']
            srv.visible = False if cfgbasic['register'] and cfgbasic['register'] == '0' else True
            srv.public = False if cfgbasic['password'] else True
            srv.logfile = cfgbasic['logfile']
            srv.econ_port = cfgbasic['econ_port']
            srv.econ_password = cfgbasic['econ_pass']
            db_add_and_commit(srv)
            
            try:
                cfgfile = open(r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig), "w")
                cfgfile.write(srvcfg)
                cfgfile.close()
            except IOError as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            res = {'success':True, 'cfg':cfgbasic, 'id':srvid, 'status': srv.status, 'alaunch': alaunch}
            res.update(cfgbasic)
            db_create_server_staff_registry(srv.id, 'Modified the configuration')
            return jsonify(res)
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@twp.route('/_get_server_config/<int:srvid>', methods=['POST'])
@check_session(level='user')
def get_server_config(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:
        srv = ServerInstance.query.get(srvid)
        if srv:
            ## Config File Text
            fullpath_fileconfig = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig)
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

@twp.route('/_get_server_issues/<int:srvid>', methods=['POST'])
@twp.route('/_get_server_issues/<int:srvid>/<int:page>', methods=['POST'])
@check_session(level='user')
def get_server_issues(srvid, page=0):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.issues:
        RPP = 10
        dbissues = Issue.query.filter(Issue.server_id==srvid).order_by(desc(Issue.date))
        numpages = int(dbissues.count()/RPP)
        dbissues_page = dbissues.offset(RPP*page).limit(RPP)
        issues = [(format_datetime(dbissue.date, 'short'), dbissue.message) for dbissue in dbissues_page]
        return jsonify({'success':True, 'issues':issues, 'pages':numpages})
    return jsonify({'notauth':True})

@twp.route('/_get_server_issues_count/<int:srvid>', methods=['POST'])
@check_session(level='user')
def get_server_issues_count(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.issues:
        issues_count = Issue.query.filter(Issue.server_id==srvid).count()
        return jsonify({'success':True, 'issues_count':issues_count})
    return jsonify({})

@twp.route('/_get_server_maps/<int:srvid>', methods=['POST'])
@check_session(level='user')
def get_server_maps(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:
        srv = ServerInstance.query.get(srvid)
        if srv:            
            ## Maps
            maps = twpl.get_mod_maps(current_app.config['SERVERS_BASEPATH'], srv.base_folder)
            return jsonify({'success':True, 'maps':maps})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@twp.route('/_get_mod_configs/<string:mod_folder>', methods=['POST'])
@check_session(level='user')
def get_mod_configs(mod_folder):
    jsoncfgs = {'configs':[]}
    cfgs = twpl.get_mod_configs(current_app.config['SERVERS_BASEPATH'], mod_folder)
    for config in cfgs:
        srv = ServerInstance.query.filter(ServerInstance.fileconfig.ilike(config),
                                            ServerInstance.base_folder.ilike(mod_folder))
        if srv.count() < 1:
            jsoncfgs['configs'].append(os.path.splitext(config)[0])
    return jsonify(jsoncfgs)

@twp.route('/_get_mod_wizard_config/<int:srvid>', methods=['POST'])
@check_session(level='user')
def get_mod_wizard_config(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.config:        
        srv = ServerInstance.query.get(srvid)
        if srv:
            fullpath = r'%s/%s/config.json' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder)
            if os.path.isfile(fullpath):
                cfgfile = open(fullpath, "r")
                config = cfgfile.read()
                cfgfile.close()
                return jsonify({'success':True, 'config':config})
            return jsonify({'success':True}) # Not exists, no problem
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    return jsonify({'notauth':True})

@twp.route('/_start_server_instance/<int:srvid>', methods=['POST'])
@check_session(level='user')
def start_server(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.start:        
        srv = ServerInstance.query.get(srvid)
        if srv:
            if not srv.bin:
                return jsonify({'error':True, 'errormsg':_('Undefined server binary file!!')})
            
            srvMatch = ServerInstance.query.filter(ServerInstance.status==1,
                                                    ServerInstance.port.ilike(srv.port),
                                                    ServerInstance.id!=srv.id)
            if srvMatch.count() > 0:
                return jsonify({'error':True, 'errormsg':_('Can\'t run two servers in the same port!')})
            
            try:
                start_server_instance(srv.base_folder, srv.bin, srv.fileconfig)
            except Exception as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            
            srv.launch_date = func.now()
            db_add_and_commit(srv)
            db_create_server_staff_registry(srv.id, 'Start server')
            time.sleep(1) # Be nice with the server...
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not exists!')})
    
    return jsonify({'notauth':True})

@twp.route('/_stop_server_instance/<int:srvid>', methods=['POST'])
@check_session(level='user')
def stop_server(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.stop:
        dbserver = ServerInstance.query.get(srvid)
        if dbserver:
            binpath = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'], dbserver.base_folder, dbserver.bin)
            proc = twpl.search_server_pid(binpath, dbserver.fileconfig)
            if proc:
                os.kill(proc, signal.SIGTERM)
                db_create_server_staff_registry(dbserver.id, 'Stop server')
                return jsonify({'success':True})
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Can\'t found server pid')})
        else:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@twp.route('/_restart_server_instance/<int:srvid>', methods=['POST'])
@check_session(level='user')
def restart_server(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.start and user_perm.stop:
        stop_server(srvid)
        start_server(srvid)
        return jsonify({'success':True})
    return jsonify({'notauth':True})

@twp.route('/_get_server_instance_log/<int:srvid>/<string:pdate>', methods=['POST'])
@check_session(level='user')
def get_current_server_instance_log(srvid, pdate=None):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.log:
        srv = ServerInstance.query.get(srvid)
        if srv:
            logcontent = ""
            if not srv.logfile:
                return jsonify({'error':True, 'errormsg':_('Logfile not defined!')})
            try:
                if srv.logfile[0] == '/':
                    fullpath = srv.logfile
                else:
                    fullpath = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder,srv.logfile)
                                
                cfgfile = open(fullpath, "r")
                logcontent = cfgfile.read()
                cfgfile.close()
            except Exception as e:
                return jsonify({'success':True, 'content':None, 'pages':None})
            
            datepages = dict()
            lines = logcontent.splitlines()
            logcontent = list()
            for line in lines:
                objMatch = re.match('^\[(.+)\]\[(.+)\]:\s(.+)$',line)
                if objMatch:
                    (date,section,message) = [int(objMatch.group(1), 16),objMatch.group(2),objMatch.group(3)]
                    dt = datetime.utcfromtimestamp(time.mktime(time.localtime(date)))
                    strDate = format_datetime(dt, "dd-MM-yyyy")
                    if not strDate in datepages:
                        datepages.update({strDate:1})
                    else:
                        datepages[strDate]+=1
                    
                    if strDate == pdate:
                        type = None
                        if re.match("^(?:client dropped|(?:.+\s)?failed)", message, re.IGNORECASE):
                            type = 'danger'
                        elif re.match("^No such command", message, re.IGNORECASE):
                            type = 'warning'
                        elif re.match("^(?:player is ready|player has entered the game|loading done|client accepted|cid=\d authed)", message, re.IGNORECASE):
                            type = 'success'
                        logcontent.append({'date':format_datetime(dt, 'short'),
                                           'section':section,
                                           'message':message,
                                           'type':type})
            
            return jsonify({'success':True, 'content':logcontent, 'pages':datepages})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@twp.route('/_get_server_instance_log/<int:srvid>/<string:code>/<string:name>', methods=['POST'])
@check_session(level='user')
def get_selected_server_instance_log(srvid, code, name):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.log:
        srv = ServerInstance.query.get(srvid)
        if srv:
            logcontent = ""
            log_file = r'%s/%s/logs/%s-%s' % (current_app.config['SERVERS_BASEPATH'], srv.base_folder, code, name)
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
                    logcontent.append({'date':format_datetime(dt),
                                       'section':section,
                                       'message':message,
                                       'type':type})
            
            return jsonify({'success':True, 'content':logcontent})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    return jsonify({'notauth':True})

@twp.route('/_send_econ_command/<int:srvid>', methods=['POST'])
@check_session(level='user')
def send_econ_command(srvid):
    cmd = request.form['cmd'] if request.form.has_key('cmd') else None
    if not cmd:
        return jsonify({'error':True, 'errormsg':'ECon command not defined!'})
        
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.econ:
        srv = ServerInstance.query.get(srvid)
        if srv and srv.econ_port and srv.econ_password:
            econ_cmd = cmd
            rcv = ''
            try:
                rcv = twpl.send_econ_command(int(srv.econ_port), srv.econ_password, econ_cmd)
            except Exception as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            db_create_server_staff_registry(srv.id, "Send ECon command '{0}'".format(econ_cmd))
            return jsonify({'success':True, 'rcv':rcv})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found or econ not configured!')})
    return jsonify({'notauth':True})

@twp.route('/_kick_player/<int:srvid>', methods=['POST'])
@twp.route('/_ban_player/<int:srvid>', methods=['POST'])
@check_session(level='user')
def kick_ban_player(srvid):
    user_perm = get_session_server_permission_level(srvid)
    if user_perm.econ:
        if not 'nick' in request.form or not request.form['nick']:
            return jsonify({'error':True, 'errormsg':_('Client player not defined!')})
        
        srv = ServerInstance.query.get(srvid)
        if srv and srv.econ_port and srv.econ_password:
            nick = request.form['nick']
            action = 'ban' if request.path.startswith('/_ban_player/') else 'kick' 
            try:
                if not twpl.send_econ_user_action(int(srv.econ_port), srv.econ_password, nick, action):
                    return jsonify({'error':True, 'errormsg':_('Can\'t found \'{0}\' player!').format(nick)})         
            except Exception as e:
                return jsonify({'error':True, 'errormsg':str(e)})
            db_create_server_staff_registry(srv.id, "{0} '{1}' via ECon".format(action.upper(),nick))
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found or econ not configured!')})
    return jsonify({'notauth':True})