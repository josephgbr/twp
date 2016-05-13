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
from flask.ext.babel import Babel, _
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func, desc
from sqlalchemy.orm import Session
db = SQLAlchemy()


class AppWebConfig(db.Model):
    __tablename__ = 'app_web_config'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    brand_url = db.Column(db.String(512))
    installed = db.Column(db.Boolean, default=False)
    
class UserServerInstancePermission(db.Model):
    __tablename__ = 'user_server_instance_permission'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    perm_id = db.Column(db.Integer, db.ForeignKey("permission_level.id"), nullable=False)
    
class PermissionLevel(db.Model):
    __tablename__ = 'permission_level'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    start = db.Column(db.Boolean, default=False)
    stop = db.Column(db.Boolean, default=False)
    log = db.Column(db.Boolean, default=False)
    econ = db.Column(db.Boolean, default=False)
    config = db.Column(db.Boolean, default=False)
    issues = db.Column(db.Boolean, default=False)
    
    def todict(self):
        return {'id': self.id,
                'name': self.name,
                'start': self.start,
                'stop': self.stop,
                'log': self.log,
                'econ': self.econ,
                'config': self.config,
                'isues': self.issues}
    
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
    
class ServerStaffRegistry(db.Model):
    __tablename__ = 'server_staff_registry'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(1024), nullable=False)
    
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, nullable=False, default=func.now())
    last_login_date = db.Column(db.DateTime)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    token = db.Column(db.String(128))
    
    def todict(self):
        return {'id': self.id,
                'create_date': str(self.create_date),
                'last_login_date': str(self.last_login_date) if self.last_login_date else _('Never'),
                'username': self.username,
                'token': self.token}
    
class ServerJob(db.Model):
    __tablename__ = 'server_job'
    id = db.Column(db.String(191), primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable = False)
    job_type = db.Column(db.Integer, nullable = False)
    job_exec = db.Column(db.String(4092))