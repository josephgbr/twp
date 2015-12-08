⚫ Teeworlds Web Panel
=
TWP is an app-web for manage your local teeworlds linux servers. Inspired by the work of '[LXC Web Panel](https://github.com/lxc-webpanel/LXC-Web-Panel)'.


Project Requirements:

**Server Side**
- [SQLite v3.x](https://www.sqlite.org/) for database
- [Flask v0.10.1](http://flask.pocoo.org/) for web development
 - [Flask APScheduler v1.1.0](https://github.com/viniciuschiele/flask-apscheduler) for periodically tasks
 - [Flask Babel v0.9](https://pythonhosted.org/Flask-Babel/) for i18n and l10n support 
- [Teeworlds Library](https://blog.mnus.de/2011/07/teeworlds-serverlist-library-for-python/) for teeworlds requests
- *tarfile, zipfile, urllib, subprocess, telnetlib, ... and many other python packages are used too!*

**Client Side**
- [Font Awesome v4.4.0](http://fontawesome.io/) for awesome icons
- [ChartJS v1.0.2](http://www.chartjs.org/) for responsive charts
- [jsSHA v2.0.2](https://github.com/Caligatio/jsSHA) for generate SHA-512 hashes
- [JQuery v1.11.3](http://jquery.com/) for easy dom interaction and much more...
 - [Bootstrap v3.3.5](http://getbootstrap.com/) for widgets and responsive design
 - [Bootbox v4.4.0](http://bootboxjs.com/) for dialogs


⚫ Installation
-
|NOTE: If you want an production deploy read '[Deploying](https://github.com/CytraL/twp#-deploying)' section.|

**Automatic (Full: builtin server)**
[
```bash
$ wget http://twp.redneboa.es -O install_twp.sh && sudo bash install_twp.sh $LOGNAME
```

**Manual (Basic)**
```bash
$ sudo apt-get install gcc python python-dev python-pip git
$ sudo pip install Flask==0.10.1
$ sudo pip install Flask-APScheduler==1.1.0
$ sudo pip install Flask-Babel==0.9
$ git clone https://github.com/CytraL/twp.git "twp"
$ cd twp
$ chmod a+x twp.py
$ ./twp.py

```

⚫ Get Started
-
0. Configure the app, see the file 'twp.conf'
1. Run or restart the app
2. Login Admin using default credentials:
 * User: admin
 * Password: admin
3. Go to settings page and change admin password

⚫ .zip/.tar.gz/folder mod structure
-
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

⚫ Enable Basic Admin Tools
-
If like kick, ban and 'econ admin' you need define 'ec_port' and 'ec_password' variables in the instance server config.


⚫ Deploying
-
See how: http://flask.pocoo.org/docs/0.10/deploying/


⚫ Limits
-
- The maximum size of upload is 16MB per mod
- The theoretical maximum time that you can have statistics on a 16-player server is 'only' of ~2,193534065×10¹² years
