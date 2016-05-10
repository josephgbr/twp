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
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import ConfigParser
import tempfile
import os
import twpl
import binascii

class TWPConfig(object):
    def __init__(self):
        config = ConfigParser.SafeConfigParser()
        config.readfp(open('twp.conf'))
        # Generate Secret Key
        self.SECRET_KEY = config.get('global', 'secret', None)
        if not self.SECRET_KEY:
            self.SECRET_KEY = binascii.hexlify(os.urandom(24)).decode()
            config.set('global', 'secret', self.SECRET_KEY)
            config.write(open('twp.conf', 'w'))
            
        self.VERSION = "0.2.0"
        self.UPLOAD_FOLDER = tempfile.mkdtemp()
        
        self.SERVERS_BASEPATH = config.get('overview', 'servers')
        self.MAX_CONTENT_LENGTH = config.getint('overview', 'max_upload_size') * 1024 * 1024
        
        self.REFRESH_TIME = config.getint('global', 'refresh_time')
        self.DEBUG = config.getboolean('global', 'debug')
        self.HOST = config.get('global', 'host')
        self.PORT = config.getint('global', 'port')
        self.THREADED = config.getboolean('global', 'threaded')
        
        self.SQLALCHEMY_DATABASE_URI = config.get('database', 'uri')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.ALLOWED_EXTENSIONS = set(['zip', 'gz', 'map'])
        self.LOGFILE = config.get('log', 'file')
        self.LOGBYTES = config.getint('log', 'maxbytes')
        self.LOGIN_MAX_TRIES = config.getint('login', 'max_tries')
        self.LOGIN_BAN_TIME = config.getint('login', 'ban_time')
        self.PARTITION = config.get('overview', 'partition')
        
        self.SESSION_TIME = config.getint('session', 'time')
        
        self.SSL = config.getboolean('global','ssl')
        self.PKEY = config.get('ssl','pkey')
        self.CERT = config.get('ssl','cert')
        self.SSL = False if not os.path.isfile(self.PKEY) or not os.path.isfile(self.CERT) else self.SSL
        
        self.SCHEDULER_VIEWS_ENABLED = False
        self.SCHEDULER_EXECUTORS = {
            'default': {
                        'type': 'threadpool', 
                        'max_workers': 5, # Optimal: Num. Cores x 2 + 1
                        }
        }
        self.SCHEDULER_JOB_DEFAULTS = {
            'coalesce': True,
            'max_instances': 1,
        }
        SCHEDULER_JOBSTORES = {
            'default': SQLAlchemyJobStore(url=self.SQLALCHEMY_DATABASE_URI)
        }
        
        self.BABEL_DEFAULT_LOCALE = 'en'
        self.SUPPORT_LANGUAGES = twpl.get_support_languages()
        
class TWPConfigTest(TWPConfig):
    def __init__(self):
        self.WTF_CSRF_ENABLED = False
        self.WTF_CSRF_CHECK_DEFAULT = False

    