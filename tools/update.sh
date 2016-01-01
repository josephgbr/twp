#!/bin/bash

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


### INSTALL TWP
INSTALL_USER=$SUDO_USER
INSTALL_DIR='/srv/twp'

if [[ ! -d "$INSTALL_DIR" ]];then
	echo 'Error: Unable to find previous installation...'
	exit 1
fi

/etc/init.d/twp stop

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

python -c 'import flask_apscheduler' &> /dev/null || {
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

tmp=$(mktemp -d)

echo 'Backuping database...'
[[ -f "$INSTALL_DIR/twp.db" ]] && cp "$INSTALL_DIR/twp.db" "$tmp" || echo "Can't backup the database!"

echo 'Removing old version...'
rm -r $INSTALL_DIR 1> /dev/null

echo 'Installing Teeworlds Web Panel...'
git clone https://github.com/CytraL/twp.git "$INSTALL_DIR"

echo 'Restore database...'
cp "$tmp/twp.db" "$INSTALL_DIR/twp.db"
rm -R "$tmp"

chown -R $INSTALL_USER:$INSTALL_USER $INSTALL_DIR

/etc/init.d/twp start

echo -e '\nUpdate complete!\n\n'
