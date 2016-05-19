# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.3.0 - Teeworlds Web Panel
##    Copyright (C) 2016  Alexandre Díaz
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
import subprocess, re, os, time, \
        signal, shutil, pytz
from flask import Flask, request, session, g, redirect, url_for, abort, \
                  flash, current_app, Blueprint
from functools import wraps
from sqlalchemy import func, desc
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask.ext.babel import Babel, _, format_datetime
from flask.ext.assets import Environment, Bundle
from flask_wtf.csrf import CsrfProtect
from twpl import BannedList
from twpl.models import *

# Global
BANLIST = BannedList()
PUBLIC_IP = twpl.get_public_ip()
SUPERUSER_ID = 1 # The hard-coded super-user id (a.k.a. administrator, or root user).
            

#################################
# SESSION CHECKS
#################################
def check_session(level):
    ''' 
        check_session validate that the active session has a logged user with the selected level.
        The levels can be:
        - 'user': Only can access registered users
        - 'admin': Only can access superuser
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not 'logged_in' in session or not session['logged_in'] or not 'uid' in session:
                abort(403)
            elif level.lower() == 'admin' and not session['uid'] == SUPERUSER_ID:
                abort(403)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def check_session_expired():
    if 'logged_in' in session and session.get('last_activity') is not None:
        now = int(time.time())
        limit = now - 60 * current_app.config['SESSION_TIME']
        last_activity = session.get('last_activity')
        if last_activity < limit:
            flash(_('Session timed out!'), 'info')
            logout()
        else:
            session['last_activity'] = now

def get_session_user():
    if not 'logged_in' in session or not session['logged_in'] or not 'uid' in session:
        return None
    return User.query.get(session['uid'])
    
def get_session_server_permission_level(srvid):
    if not 'logged_in' in session or not session['logged_in']:
        return PermissionLevel()
    if session['uid'] == SUPERUSER_ID:
        return PermissionLevel().sudo()
    usip = UserServerInstancePermission.query.filter(UserServerInstancePermission.user_id == session['uid'],
                                                    UserServerInstancePermission.server_id == srvid)
    if usip.count() < 1:
        return PermissionLevel()
    
    usip = usip.one()
    if not usip.perm:
        return PermissionLevel()
    return usip.perm


#################################
# JOBS
#################################
def analyze_all_server_instances(app):
    with app.app_context():
        Player.query.update({Player.status:0})
        ServerInstance.query.update({ServerInstance.status:0})
        
        # Check Server & Player Status
        netstat = twpl.netstat()
        for conn in netstat:
            if not conn[2]:
                continue
            objMatch = re.match("^.+\/([^\/]+)\/(.+)$", conn[2])
            if objMatch:
                (base_folder,bin) = [objMatch.group(1), objMatch.group(2)]
                srv = ServerInstance.query.filter(ServerInstance.port.ilike(conn[0]),
                                                    ServerInstance.base_folder.ilike(base_folder),
                                                    ServerInstance.bin.ilike(bin))
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
                        
                        playersMatch = Player.query.filter(Player.name.ilike(ntplayer.name))
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
        servers = ServerInstance.query.filter(ServerInstance.status==0, ServerInstance.alaunch==True).all()
        for dbserver in servers:
            modfolder = r'%s/%s' % (current_app.config['SERVERS_BASEPATH'], dbserver.base_folder)
            if not os.path.isdir(modfolder):
                continue
                    
            if not os.path.isfile(r'%s/%s' % (modfolder, dbserver.bin)):
                nissue = Issue(server_id=dbserver.id,
                               message="Can't start: No server binary selected!")
                db.session.add(nissue)
                continue
            
            if dbserver.logfile:
                current_time_hex = hex(int(time.time())).split('x')[1]
                logs_folder = r'%s/%s/logs' % (current_app.config['SERVERS_BASEPATH'], dbserver.base_folder)
                log_file = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'], dbserver.base_folder, dbserver.logfile)
                # Create logs folder if not exists
                if not os.path.isdir(logs_folder):
                    os.makedirs(logs_folder)
                # Move current log to logs folder
                if os.path.isfile(log_file):
                    shutil.move(log_file, r'%s/%s-%s' % (logs_folder, current_time_hex, dbserver.logfile))
                nissue = Issue(server_id=dbserver.id,
                               message="%s <a class='btn btn-xs btn-primary pull-right' href='/log/%d/%s/%s'>View log</a>" % ('Server Offline', 
                                                                                                                              dbserver.id, 
                                                                                                                              current_time_hex, 
                                                                                                                              dbserver.logfile))
                db.session.add(nissue)
            else:
                nissue = Issue(server_id=dbserver.id,
                               message='Server Offline')
                db.session.add(nissue)

            # Open server
            dbserver.launch_date = func.now()
            db.session.add(dbserver)
            start_server_instance(dbserver.base_folder, dbserver.bin, dbserver.fileconfig) 
        
        db.session.commit()
        

#################################
# TOOLS
#################################  
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']
           
#def shutdown_all_server_instances():
#    netstat = twpl.netstat()
#    for conn in netstat:
#        servers = query_db("SELECT base_folder,bin FROM servers WHERE port=?", [conn[0]])
#        for srv in servers:
#            if conn[2].endswith('%s/%s' % (server['base_folder'],server['bin'])):
#                os.kill(int(conn[1]), signal.SIGTERM)

def start_server_instance(base_folder, bin, fileconfig):
    binpath = r'%s/%s/%s' % (current_app.config['SERVERS_BASEPATH'], base_folder, bin)
    # Force it! (prevent zombie state)
    proc = twpl.search_server_pid(binpath, fileconfig)
    if proc:
        os.kill(proc, signal.SIGKILL)
    
    subprocess.Popen([binpath, '-f', fileconfig],
                    cwd=r'%s/%s/' % (current_app.config['SERVERS_BASEPATH'], base_folder),
                    close_fds=True,
                    preexec_fn=os.setsid)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(_("Error in the '{0}' field - {1}").format(
                getattr(form, field).label.text,
                error
            ), 'danger')


#################################
# FLASK GENERAL
#################################
twp = Blueprint('twp', __name__, static_folder='static/')
from webcontroller import *
from webcontroller.public import logout

# Create Flask App
def create_app(twpconf):
    app = Flask(__name__)
    app.config.from_object(twpconf)
    app.register_blueprint(twp)
    db.init_app(app)
    babel = Babel(app)
    assets = Environment(app)
    csrf = CsrfProtect(app)
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job('twp:analyze_all_server_instances', 
                      analyze_all_server_instances, 
                      trigger={'second':30, 'type':'cron'}, 
                      replace_existing=True, 
                      args=(app,))

    # Check Servers path
    app.config['SERVERS_BASEPATH'] = r'%s/%s' % (app.root_path, 
                                                 app.config['SERVERS_BASEPATH']) if not app.config['SERVERS_BASEPATH'][0] == '/' else app.config['SERVERS_BASEPATH']
    if not os.path.isdir(app.config['SERVERS_BASEPATH']):
        os.makedirs(app.config['SERVERS_BASEPATH'])
    
    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(current_app.config['SUPPORT_LANGUAGES'])
    @babel.timezoneselector
    def get_timezone():
        try:
            sess_user = get_session_user()
            if sess_user and sess_user.timezone:
                tzstr = sess_user.timezone
            elif 'timezone' in session:
                tzstr = session.get('timezone')
            else:
                tzstr = pytz.country_timezones[request.accept_languages.best_match(current_app.config['SUPPORT_LANGUAGES'])][0]
        except:
            return None
        else:
            return tzstr
        
    return app

#################################
# FLASK CALLBACKS
#################################
@twp.context_processor
def utility_processor():
    def get_mod_instances(mod_folder):
        servers = ServerInstance.query.filter(ServerInstance.base_folder.ilike(mod_folder)).all()
        return servers
    def get_mod_binaries(mod_folder):
        return twpl.get_mod_binaries(current_app.config['SERVERS_BASEPATH'], mod_folder)
    def get_app_config():
        return AppWebConfig.query.get(1)
    def get_timezones():
        return pytz.all_timezones
    
    return dict(get_mod_instances=get_mod_instances, 
                get_mod_binaries=get_mod_binaries,
                get_app_config=get_app_config,
                get_uid_permission_level=get_session_server_permission_level,
                SUPERUSER_ID=SUPERUSER_ID,
                format_datetime=format_datetime,
                get_timezones=get_timezones)
    
@twp.before_request
def before_request():
    # Session Banned?
    BANLIST.refresh()
    if not request.path.startswith('/banned') and BANLIST.find(request.remote_addr):
        abort(403)
    
    # Session Expired?
    check_session_expired()
    
    # Set page language
    if request.view_args and 'lang_code' in request.view_args:
        g.current_lang = request.view_args['lang_code']
        request.view_args.pop('lang_code')
        
    # Need Installation?
    app_config = AppWebConfig.query.order_by(desc(AppWebConfig.id)).one()
    if not app_config.installed \
        and not request.path.startswith('/install') \
        and not request.path.startswith('/static') \
        and not request.path.startswith('/_finish_installation'):
        return redirect(url_for('twp.installation'))

#@twp.teardown_request
#def teardown_request(exception):