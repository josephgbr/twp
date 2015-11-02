+ Teeworlds Web Panel
=============================================
TWP is an app-web for manage your local teeworlds linux servers. Inspired by the work of 'LXC Web Panel'.

The project uses:

**Server Side**
- [SQLite v3.x](https://www.sqlite.org/) for database
- [Flask v0.10.1](http://flask.pocoo.org/) for web development
 - [Flask APScheduler v1.1.0](https://github.com/viniciuschiele/flask-apscheduler) for periodically tasks
- [Teeworlds Library](https://blog.mnus.de/2011/07/teeworlds-serverlist-library-for-python/) for teeworlds requests
- *tarfile, zipfile, urllib, subprocess, os, ... and many other python packages are used too!*

**Client Side**
- [JQuery v1.11.3](http://jquery.com/) for easy dom interaction and more...
 - [Bootstrap v3.3.5](http://getbootstrap.com/) for widgets and responsive design
  - [Bootbox v4.4.0](http://bootboxjs.com/) for dialogs
- [Font Awesome v4.4.0](http://fontawesome.io/) for awesome icons