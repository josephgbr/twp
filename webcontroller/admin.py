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
                get_session_server_permission_level, allowed_file
import time, os, shutil, binascii
from flask import request, session, redirect, url_for, \
                  flash, jsonify, current_app
from flask.ext.babel import Babel, _, format_datetime
from werkzeug import secure_filename
from twpl.models import *
                  
#################################
# GET
#################################
@twp.route('/install_mod', methods=['POST'])
@check_session(level='admin')
def install_mod():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('twp.servers')
    filename = None
    if 'url' in request.form and not request.form['url'] == '':
        try:
            filename = secure_filename(twpl.download_mod_from_url(request.form['url'], current_app.config['UPLOAD_FOLDER']))
        except Exception as e:
            flash(_("Error: {0}").format(str(e)), 'danger')
    else:  
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            else:
                flash(_('Error: File type not allowed!'), 'danger')
        else:
            flash(_('Error: No file detected!'), 'danger')
            
    if filename:
        status,errors = twpl.install_server_mod(r'%s/%s' % (current_app.config['UPLOAD_FOLDER'], filename), 
                                               current_app.config['SERVERS_BASEPATH'])
        if status:
            flash(_('Mod installed successfully'), 'info')
        elif not status and not errors:
            flash(_('Error: Can\'t install selected mod package'), 'danger')
        else:
            msg = _('Error: Package not have the followed folders:')+' '
            for err in errors:
                msg += err+', '
            flash(msg, 'danger')
    return redirect(current_url)


#################################
# POST
#################################
@twp.route('/_remove_mod', methods=['POST'])
@check_session(level='admin')
def remove_mod():
    if 'folder' in request.form:
        fullpath_folder = r'%s/%s' % (current_app.config['SERVERS_BASEPATH'], request.form['folder'])
        if os.path.exists(fullpath_folder):
            servers = ServerInstance.query.filter(ServerInstance.base_folder.ilike(request.form['folder'])).all()
            for srv in servers:
                stop_server(srv.id)
                remove_server_instance(srv.id,1)
            shutil.rmtree(fullpath_folder)
            return jsonify({'success':True})
        return jsonify({'error':True, 'errormsg':_('Error: Folder mod not exists!')})
    return jsonify({'error':True, 'errormsg':_('Error: Old or new password not defined!')})

@twp.route('/_create_user_slot', methods=['POST'])
@check_session(level='admin')
def create_user_slot():
    token = binascii.hexlify(os.urandom(24)).decode()
    user = User(username=token, password=token, token=token) # TODO: Perhaps best a table for slots?
    db_add_and_commit(user)
    if user.id:
        return jsonify({'success':True, 'user':user.to_dict(), 'create_date_format':format_datetime(user.create_date)})
    return jsonify({'error':True,'errormsg':_("Can't generate user slot!")})

@twp.route('/_remove_user/<int:uid>', methods=['POST'])
@check_session(level='admin')
def remove_user(uid):
    if uid == SUPERUSER_ID:
        return jsonify({'error':True,'errormsg':_("Can't remove superuser!")})
    user = User.query.get(uid)
    if user:
        db_delete_and_commit(user)
        return jsonify({'success':True})
    return jsonify({'error':True,'errormsg':_("Can't found user")})

@twp.route('/_change_permission_level', methods=['POST'])
@check_session(level='admin')
def change_permission_level():
    perm_att = request.form['perm'].lower() if request.form.has_key('perm') else None
    id = request.form['id'] if request.form.has_key('id') else None
    if not perm_att or not id:
        return jsonify({ 'error':True, 'errormsg':_('Invalid params!') })
    
    perm = PermissionLevel.query.get(id)
    if perm_att == 'start':
        perm.start = not perm.start
    elif perm_att == 'stop':
        perm.stop = not perm.stop
    elif perm_att == 'config':
        perm.config = not perm.config
    elif perm_att == 'econ':
        perm.econ = not perm.econ
    elif perm_att == 'issues':
        perm.issues = not perm.issues
    elif perm_att == 'log':
        perm.log = not perm.log
    else:
        return jsonify({ 'error':True, 'errormsg':_('Invalid params!') })
    
    db_add_and_commit(perm)
    return jsonify({ 'success':True })
      
@twp.route('/_create_permission_level', methods=['POST'])
@check_session(level='admin')
def create_permission_level():
    name = request.form['name'] if request.form.has_key('name') else None
    if not name:
        return jsonify({ 'error':True, 'errormsg':_('Permission need a name!') })
    
    # Check unique permission level name
    perm_id = PermissionLevel.query.filter(PermissionLevel.name.ilike(request.form['name']))
    if perm_id.count() > 0:
        return jsonify({ 'error':True, 'errormsg':_("Permission Level name need be unique") })
    
    # Check unique permission level parameters
    #start_serv = True if request.form.has_key('start') and request.form['start'] else False
    #stop_serv = True if request.form.has_key('stop') and request.form['stop'] else False
    #view_config = True if request.form.has_key('config') and request.form['config'] else False
    #use_econ = True if request.form.has_key('econ') and request.form['econ'] else False
    #view_issues = True if request.form.has_key('issues') and request.form['issues'] else False
    #view_log = True if request.form.has_key('log') and request.form['log'] else False
    #
    #perm_id = PermissionLevel.query.filter(PermissionLevel.start == start_serv,
    #                                        PermissionLevel.stop == stop_serv,
    #                                        PermissionLevel.config == view_config,
    #                                        PermissionLevel.econ == use_econ,
    #                                        PermissionLevel.issues == view_issues,
    #                                        PermissionLevel.log == view_log)
    #if perm_id.count() > 0:
    #    return jsonify({ 'error':True, 'errormsg':_("Already have a permission with the same parameters!") })
    
    # Create permisson level
    perm_level = PermissionLevel(name=request.form['name'])
    db_add_and_commit(perm_level)
    return jsonify({'success':True, 'perm':perm_level.to_dict()})
    
@twp.route('/_remove_permission_level/<int:id>', methods=['POST'])
@check_session(level='admin')
def remove_permission_level(id):
    perm_id = PermissionLevel.query.get(id)
    if not perm_id:
        return jsonify({'error':True, 'errormsg':_('Invalid Permission')})
    db_delete_and_commit(perm_id)
    return jsonify({'success':True})

@twp.route('/_get_user_servers_level/<int:uid>', methods=['POST'])
@check_session(level='admin')
def get_user_servers_level(uid):
    perm_list = []
    perms = UserServerInstancePermission.query.filter(UserServerInstancePermission.user_id == uid).all()
    for perm in perms:
        perm_list.append((perm.server_id, perm.perm_id))
    return jsonify({ 'success':True, 'perms':perm_list })

@twp.route('/_set_user_server_level/<int:uid>/<int:srvid>', methods=['POST'])
@check_session(level='admin')
def _set_user_server_level(uid, srvid):
    if uid == SUPERUSER_ID:
        return jsonify({ 'error':True, 'errormsg':"Can't define permission for superuser!" })
    
    perm_id = request.form['perm_id'] if request.form.has_key('perm_id') else None
    if not perm_id:
        return jsonify({ 'error':True, 'errormsg':'Permission ID not defined!' })
    
    perms = UserServerInstancePermission.query.filter(UserServerInstancePermission.user_id == uid,
                                                      UserServerInstancePermission.server_id == srvid)
    if perms.count() > 0:
        perm = perms.one()
        if not perm_id == -1:
            perm.perm_id = perm_id
            db_add_and_commit(perm)
        else:
            db_delete_and_commit(perm)
    elif not perm_id == -1:
        perm = UserServerInstancePermission(user_id=uid, server_id=srvid, perm_id=perm_id)
        db_delete_and_commit(perm)
    return jsonify({ 'success':True })

@twp.route('/_create_server_instance/<string:mod_folder>', methods=['POST'])
@check_session(level='admin')
def create_server_instance(mod_folder):
    fileconfig = request.form['fileconfig']
    if not fileconfig or fileconfig == "":
        return jsonify({'error':True, 'errormsg':_('Invalid configuration file name.')})
    
    fileconfig = '%s.conf' % fileconfig
    fullpath_fileconfig = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'],mod_folder,fileconfig)
    
    # Search for mod binaries, if only exists one use it
    bin = None
    srv_bins = twpl.get_mod_binaries(current_app.config['SERVERS_BASEPATH'], mod_folder)
    if srv_bins and len(srv_bins) == 1:
        bin = srv_bins[0]
    
    # Check if other server are using the same configuration file
    srvMatch = ServerInstance.query.filter(ServerInstance.fileconfig.ilike(fileconfig), 
                                            ServerInstance.base_folder.ilike(mod_folder))
    if srvMatch.count() > 0:
        return jsonify({'error':True, 
                        'errormsg':_("Can't exists two servers with the same configuration file.<br/>"+\
                                     "Please change configuration file name and try again.")})
                
    cfgbasic = twpl.get_data_config_basics(fullpath_fileconfig)
    
    # Check if the logfile are be using by other server with the same base_folder
    if cfgbasic['logfile']:
        srvMatch = ServerInstance.query.filter(ServerInstance.logfile.ilike(cfgbasic['logfile']), 
                                                ServerInstance.base_folder.ilike(mod_folder))
        if srvMatch.count() > 0:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exist two servers with the same log file.<br/>"+\
                                         "Please check configuration and try again.")})
        
    # Check if the econ_port are be using by other server
    if cfgbasic['econ_port']:
        srvMatch = ServerInstance.query.filter(ServerInstance.econ_port==cfgbasic['econ_port'])
        if srvMatch.count() > 0:
            return jsonify({'error':True, 
                            'errormsg':_("Can't exist two servers with the same 'ec_port'.<br/>"+\
                                         "Please check configuration and try again.")})
    
    # Check if the port are be using by other server with the same base_folder
    fport = int(cfgbasic['port'])
    while True:
        srvMatch = ServerInstance.query.filter(ServerInstance.port.ilike(str(fport)), 
                                                ServerInstance.base_folder.ilike(mod_folder))
        if srvMatch.count() < 1:
            break
        fport += 1

    try:
        if cfgbasic['name'] == u'unnamed server':
            cfgbasic['name'] = u'Server created with Teeworlds Web Panel'
            twpl.write_config_param(fullpath_fileconfig, u'sv_name', cfgbasic['name'])
        if not fport == int(cfgbasic['port']):
            cfgbasic['port'] = unicode(str(fport))
            twpl.write_config_param(fullpath_fileconfig, u'sv_port', cfgbasic['port'])
    except Exception, e:
         return jsonify({'error':True, 'errormsg':str(e)})
        
    # If all checks good, create the new instance
    nserver = ServerInstance(fileconfig=fileconfig,
                             base_folder=mod_folder,
                             bin=bin,
                             port=str(fport),
                             name=cfgbasic['name'],
                             gametype=cfgbasic['gametype'],
                             visible=False if cfgbasic['register'] and cfgbasic['register'] == '0' else True,
                             public=False if cfgbasic['password'] else True,
                             logfile=cfgbasic['logfile'],
                             econ_port=cfgbasic['econ_port'],
                             econ_password=cfgbasic['econ_pass'],
                             status=0)
    db_add_and_commit(nserver)
    return jsonify({'success':True})

@twp.route('/_remove_server_instance/<int:id>/<int:delconfig>', methods=['POST'])
@check_session(level='admin')
def remove_server_instance(id, delconfig=0):
    srv = ServerInstance.query.get(id)
    if not srv:
        return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
    
    if delconfig == 1:
        os.unlink(r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'],srv.base_folder,srv.fileconfig))
    
    db_delete_and_commit(srv)
    return jsonify({'success':True})