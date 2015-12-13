# Teeworlds Web Panel
TWP is an app-web for manage your local teeworlds linux servers. Inspired by the work of '[LXC Web Panel](https://github.com/lxc-webpanel/LXC-Web-Panel)'.


Project Requirements:

**Server Side**
- [SQLite v3.x](https://www.sqlite.org/) for database
- [Flask v0.10.1](http://flask.pocoo.org/) for web development
 - [Flask APScheduler v1.1.0](https://github.com/viniciuschiele/flask-apscheduler) for periodically tasks
 - [Flask Babel v0.9](https://pythonhosted.org/Flask-Babel/) for i18n and l10n support 
- [Teeworlds Serverlist Library](https://blog.mnus.de/2011/07/teeworlds-serverlist-library-for-python/) for teeworlds requests
- [Pillow v3.0.0](https://pypi.python.org/pypi/pngcanvas/1.0.3) for generate png images
- *tarfile, zipfile, urllib, subprocess, telnetlib, ... and many other python packages are used too!*

**Client Side**
- [Font Awesome v4.5.0](http://fontawesome.io/) for awesome icons
- [MorrisJS v0.5.1](http://morrisjs.github.io/morris.js/) for responsive charts
- [jsSHA v2.0.2](https://github.com/Caligatio/jsSHA) for generate SHA-512 hashes
- [JQuery v1.11.3](http://jquery.com/) for easy dom interaction and much more...
 - [Bootstrap v3.3.5](http://getbootstrap.com/) for widgets and responsive design
 - [Bootbox v4.4.0](http://bootboxjs.com/) for dialogs

### Installation (Debian based distributions)
_NOTE: If you want an production deploy read '[Deploying](https://github.com/CytraL/twp#-deploying)' section._

**Automatic (Full) --Warning: builtin server--**
```bash
$ wget http://twp.redneboa.es -O install_twp.sh && sudo bash install_twp.sh $LOGNAME
```

**Manual (Basic)**
```bash
$ sudo apt-get install gcc python python-dev python-pip git libjpeg-dev zlib1g-dev
$ sudo pip install Flask==0.10.1
$ sudo pip install Flask-APScheduler==1.1.0
$ sudo pip install Flask-Babel==0.9
$ sudo pip install Pillow==3.0.0
$ git clone https://github.com/CytraL/twp.git "twp"
$ cd twp
$ chmod a+x twp.py
$ ./twp.py

```

### Get Started
0. Configure the app, see the file 'twp.conf'
1. Run or restart the app
2. Login Admin using default credentials:
 * User: admin
 * Password: admin
3. Go to settings page and change admin password

### .zip/.tar.gz/folder mod structure
```
mod_folder
  - data
    + mapres
    + maps
  config.cfg
  license.txt
  readme.txt
  teeworlds_srv
```

### Enable Basic Admin Tools
If like kick, ban and 'econ admin' you need define 'ec_port' and 'ec_password' variables in the instance server config.

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
- Edit .po file using for example '[poedit](http://poedit.net/download)'
- Compile:
```bash
$ pybabel compile -d translations
```

_** If changes strings on the app, you will need update current translations_
```bash
$ pybabel update -i messages.pot -d translations
```

### Limits
- The default maximum size of upload is 16MB per mod
- The theoretical maximum time that you can have statistics on a 16-player server is 'only' of ~2,193534065×10¹² years
