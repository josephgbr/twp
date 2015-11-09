+ Teeworlds Web Panel
=============================================
TWP is an app-web for manage your local teeworlds linux servers. Inspired by the work of 'LXC Web Panel'.


Project Requirements:
**Server Side**
- [SQLite v3.x](https://www.sqlite.org/) for database
- [Flask v0.10.1](http://flask.pocoo.org/) for web development
 - [Flask APScheduler v1.1.0](https://github.com/viniciuschiele/flask-apscheduler) for periodically tasks
- [Teeworlds Library](https://blog.mnus.de/2011/07/teeworlds-serverlist-library-for-python/) for teeworlds requests
- *tarfile, zipfile, urllib, subprocess, telnetlib, ... and many other python packages are used too!*

**Client Side**
- [JQuery v1.11.3](http://jquery.com/) for easy dom interaction and more...
 - [Bootstrap v3.3.5](http://getbootstrap.com/) for widgets and responsive design
 - [Bootbox v4.4.0](http://bootboxjs.com/) for dialogs
- [Font Awesome v4.4.0](http://fontawesome.io/) for awesome icons
- [ChartJS v1.0.2](http://www.chartjs.org/) for charts


+ Installation
=============================================
**Using Script**

*More information Soon...*

**Manual**
```bash
$ sudo apt-get install gcc python python-pip git
$ sudo pip install Flask==0.10.1
$ sudo pip install Flask-APScheduler==1.1.0
$ git clone -b 0.1.0b https://github.com/CytraL/twp.git "twp"
$ cd twp
$ chmod +x twp.py
$ ./twp.py
```

+ Get Started
=============================================
0. Configure the app, see the file 'twp.conf'
1. Run or restart the app
2. Login Admin using default credentials:
 * User: admin
 * Password: admin
3. Go to settings page and change admin password


+ Advance Deploy (For production environments)
=============================================
See how: (http://flask.pocoo.org/docs/0.10/deploying/)