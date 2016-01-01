#!/bin/bash
echo '████████╗  ██╗    ██╗  ██████╗ '
echo '╚══██╔══╝  ██║    ██║  ██╔══██╗'
echo '   ██║     ██║ █╗ ██║  ██████╔╝'
echo '   ██║     ██║███╗██║  ██╔═══╝ '
echo '   ██║     ╚███╔███╔╝  ██║     '
echo '   ╚═╝      ╚══╝╚══╝   ╚═╝     '
echo '               Teeworlds Web Panel Automatic installer'
echo -e "\n"


if [[ -z $SUDO_USER ]]; then
	echo -e "Error, can't read user installation!"
	exit 1
fi

if [[ "$UID" -ne "0" ]];then
	echo 'You must be root to install Teeworlds Web Panel!'
	exit 1
fi

if [ "$SUDO_USER" == "root" ]; then
	echo "Error, install for 'root' user it's a security issue... change user and try again."
	exit 1
fi

read -r -p "Do you want install TWP using '$SUDO_USER' user? [Y/n]: " response
if [[ $response =~ [nN] ]]; then
	exit 0
fi


### INSTALL TWP
INSTALL_USER=$SUDO_USER
INSTALL_DIR='/srv/twp'

if [[ -d "$INSTALL_DIR" ]];then
	echo "You already have Teeworlds Web Panel installed. You'll need to remove $INSTALL_DIR if you want to install"
	exit 1
fi

echo 'Installing requirements. Please, wait...'

apt-get update 1> /dev/null

hash gcc &> /dev/null || {
	echo '+ Installing gcc'
	apt-get install -y gcc 1> /dev/null
}

echo '+ Installing libjpeg'
apt-get install -y libjpeg-dev 1> /dev/null

echo '+ Installing zlib1g'
apt-get install -y zlib1g-dev 1> /dev/null

echo '+ Installing Python-dev'
apt-get install -y python-dev 1> /dev/null

hash python &> /dev/null || {
	echo '+ Installing Python'
	apt-get install -y python 1> /dev/null
}

hash pip &> /dev/null || {
	echo '+ Installing Python pip'
	apt-get install -y python-pip 1> /dev/null
}

python -c 'import flask' &> /dev/null || {
	echo '| + Flask Python...'
	pip install flask==0.10.1 1> /dev/null
}

python -c 'import Flask_APScheduler' &> /dev/null || {
	echo '| + Flask-APScheduler Python...'
	pip install Flask-APScheduler==1.3.3 1> /dev/null
}

python -c 'import flask.ext.babel' &> /dev/null || {
	echo '| + Flask-Babel Python...'
	pip install Flask-Babel==0.9 1> /dev/null
}

python -c 'import PIL' &> /dev/null || {
	echo '| + Pillow Python...'
	pip install Pillow==3.0.0 1> /dev/null
}


echo 'Cloning Teeworlds Web Panel...'
hash git &> /dev/null || {
	echo '+ Installing Git'
	apt-get install -y git 1> /dev/null
}

git clone https://github.com/CytraL/twp.git "$INSTALL_DIR"
chown -R $INSTALL_USER:$INSTALL_USER $INSTALL_DIR

echo -e '\nInstallation complete!\n\n'


### DAEMON
echo 'Adding /etc/init.d/twp...'

cat > '/etc/init.d/twp' <<EOF
#!/bin/bash
# Copyright (c) 2013 LXC Web Panel
# All rights reserved.
#
# Author: Elie Deloumeau
# Modificated for TWP by Alexandre Díaz (dev@redneboa.es)
#
# /etc/init.d/twp
#
### BEGIN INIT INFO
# Provides: twp
# Required-Start: \$local_fs \$network
# Required-Stop: \$local_fs
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: TWP Start script
### END INIT INFO


WORK_DIR="$INSTALL_DIR"
SCRIPT="twp.py"
DAEMON="/usr/bin/python \$WORK_DIR/\$SCRIPT"
PIDFILE="/var/run/twp.pid"
USER="$INSTALL_USER"

function start () {
	echo -n 'Starting server...'
	/sbin/start-stop-daemon --start --pidfile \$PIDFILE \\
		--user \$USER --group \$USER \\
		-b --make-pidfile \\
		--chuid \$USER \\
		--chdir \$WORK_DIR \\
		--exec \$DAEMON
	echo 'done.'
	}

function stop () {
	echo -n 'Stopping server...'
	/sbin/start-stop-daemon --stop --pidfile \$PIDFILE --signal KILL --verbose
	echo 'done.'
}


case "\$1" in
	'start')
		start
		;;
	'stop')
		stop
		;;
	'restart')
		stop
		start
		;;
	*)
		echo 'Usage: /etc/init.d/twp {start|stop|restart}'
		exit 0
		;;
esac

exit 0
EOF

chmod +x '/etc/init.d/twp'
update-rc.d twp defaults &> /dev/null
echo -e 'Done\n'
/etc/init.d/twp start

### END
echo 'Connect you on http://your-ip-address:8000/ (Example: http://localhost:8000)'
echo 'User: admin'
echo 'Password: admin'
echo -e "*** DON'T FORGET CHANGE DEFAULT ADMIN PASSWORD!!! ***\n\n"