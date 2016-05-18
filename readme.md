# Teeworlds Web Panel [![Circle CI](https://circleci.com/gh/CytraL/twp/tree/0.3.0.svg?style=svg)](https://circleci.com/gh/CytraL/twp/tree/0.3.0)
TWP is an app-web for manage your local teeworlds linux servers. Inspired by the work of '[LXC Web Panel](https://github.com/lxc-webpanel/LXC-Web-Panel)'.


Project Requirements:

**Server Side**
- [SQLite](https://www.sqlite.org/) for default database
- [Flask v0.10.1](http://flask.pocoo.org/) for web development
 - [Flask APScheduler v1.3.7](https://github.com/viniciuschiele/flask-apscheduler) for periodically tasks
 - [Flask Babel v0.10](https://pythonhosted.org/Flask-Babel/) for i18n and l10n support
 - [Flask WTF v0.12](https://flask-wtf.readthedocs.io/en/latest/) for CSRF protection and recaptcha
 - [Flask Assets v0.11](http://flask-assets.readthedocs.io/) for integrate webassets (Asset management for Python web development)
 - [Flask SQLAlchemy v2.1](http://flask-sqlalchemy.pocoo.org/2.1/) for SQLAlchemy ORM support
- [JSMin](https://pypi.python.org/pypi/jsmin) a javascript minifier
- [CSSMin](https://pypi.python.org/pypi/cssmin/) a python port of the YUI CSS compression algorithm
- [Teeworlds Serverlist Library](https://blog.mnus.de/2011/07/teeworlds-serverlist-library-for-python/) for teeworlds requests
- [Pillow v3.2.0](https://pypi.python.org/pypi/Pillow/3.2.0) for generate png images
- [MergeDict v0.2.0](https://pypi.python.org/pypi/mergedict/0.2.0) for make the life easier with python dictionaries
- *tarfile, zipfile, urllib, subprocess, telnetlib, ... and many other python packages are used too!*

**Client Side**
- [Font Awesome v4.6.1](http://fontawesome.io/) for awesome icons
- [ChartistJS v0.9.7](http://gionkunz.github.io/chartist-js/) for responsive charts
- [MomentJS v2.13.0](http://momentjs.com/) for easy date manage
- [Clipboard v1.5.10](http://clipboardjs.com) for copy to clipboard
- [jsSHA v2.0.2](http://caligatio.github.io/jsSHA/) for generate SHA-512 hashes
- [JQuery v1.12.0](http://jquery.com/) for easy dom interaction and much more...
 - [Bootstrap v3.3.6](http://getbootstrap.com/) for widgets and responsive design
 - [Bootbox v4.4.0](http://bootboxjs.com/) for dialogs
 - [Bootstrap Colorpicker v2.3.2](http://mjolnic.com/bootstrap-colorpicker/)
 - [Select2 v4.0.2](https://select2.github.io) - JQuery replacement for select boxes

### Installation (Debian based distributions)
_NOTE: If you want an production deploy read '[Deploying](https://github.com/CytraL/twp#-deploying)' section._

**Automatic (Full) --Warning: builtin server--**
```bash
$ wget http://cytral.github.io/twp/tools/install.sh && sudo bash install.sh
```
or...
```bash
$ wget http://cytral.github.io/twp/tools/install.sh && su -c "bash install.sh $USER"
```

**Manual (Basic)**
```bash
$ sudo apt-get install gcc python python-dev python-pip git libjpeg-dev zlib1g-dev libfreetype6-dev
$ git clone https://github.com/CytraL/twp.git
$ cd twp
$ sudo pip install -r requirements.txt
$ chmod a+x twp.py
$ ./twp.py

```

### Get Started
0. Configure the app, see the file 'twp.conf'
1. Run or restart the app

### .zip/.tar.gz/folder mod structure
```
mod_folder
  - data
    + mapres
    + maps
  config.cfg*
  license.txt*
  readme.txt*
  teeworlds_srv
  config.json*
```
_(*) Not required but recommended_

### .zip/.tar.gz map packages
TWP allows you to upload maps in packages instead of using an standalone .map file. The package only can contain .map files (whitout folders)

### Enable Basic Admin Tools
If like kick, ban and 'econ admin' you need define 'ec_port' and 'ec_password' variables in the instance server config.

### Available RDBMS/ORDBMS
You can change the 'uri' param in 'database' on 'twp.conf' file for use most of these dialects: 
http://docs.sqlalchemy.org/en/latest/dialects/

### Deploying
See how: http://flask.pocoo.org/docs/0.10/deploying/

### Translations
_You will need install 'pybabel'_


** Do this using the project directory!

- Generate .pot file
```bash
$ pybabel extract -F babel.cfg -o messages.pot .
```
- Generate folder structure and .po file (Omit if you already do it)
```bash
$ pybabel init -i messages.pot -d translations -l <language code: ISO 639-1>
```

_** Otherwise, if changed strings on the source, you will need update current translations_
```bash
$ pybabel update -i messages.pot -d translations
```

- Edit .po file(s) using for example '[poedit](http://poedit.net/download)'

- Compile:
```bash
$ pybabel compile -d translations
```

### Limits
- The default maximum size of upload is 16MB per mod
- The theoretical maximum time that you can have statistics on a 16-player server is 'only' of ~2,193534065×10¹² years (with sqlite)
