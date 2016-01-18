import ConfigParser
import tempfile
import os
import twpl

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
        # Servers path
        self.SERVERS_BASEPATH = config.get('overview', 'servers')
        if not os.path.isdir(self.SERVERS_BASEPATH):
            os.makedirs(self.SERVERS_BASEPATH)
        
        self.VERSION = "0.2.0"
        self.BRAND_NAME = config.get('overview', 'brand_name')
        self.BRAND_URL = config.get('overview', 'brand_url')
        self.REFRESH_TIME = config.getint('global', 'refresh_time')
        self.DEBUG = config.getboolean('global', 'debug')
        self.HOST = config.get('global', 'host')
        self.PORT = config.getint('global', 'port')
        self.THREADED = config.getboolean('global', 'threaded')
        self.SQLALCHEMY_DATABASE_URI = config.get('database', 'file')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.UPLOAD_FOLDER = tempfile.mkdtemp()
        self.MAX_CONTENT_LENGTH = config.getint('overview', 'max_upload_size') * 1024 * 1024
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
            'default': {'type': 'threadpool', 'max_workers': 5} # Optimal: Num. Cores x 2 + 1
        }
        self.SCHEDULER_JOB_DEFAULTS = {
            'coalesce': True,
            'max_instances': 1
        }
        
        self.BABEL_DEFAULT_LOCALE = 'en'
        self.SUPPORT_LANGUAGES = twpl.get_support_languages()