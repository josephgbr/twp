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

if hash systemctl &> /dev/null;
then
	service twp stop
else
	/etc/init.d/twp stop
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

echo '+ Installing libfreetype6-dev'
apt-get install -y libfreetype6-dev 1> /dev/null

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

tmp=$(mktemp -d)

[[ -f "$INSTALL_DIR/twp.service" ]] && cp "$INSTALL_DIR/twp.service" "$tmp"

echo 'Backuping database...'
[[ -f "$INSTALL_DIR/twp.db" ]] && cp "$INSTALL_DIR/twp.db" "$tmp" || echo "Can't backup the database!"

echo 'Backuping servers...'
[[ -d "$INSTALL_DIR/servers" ]] && cp -r "$INSTALL_DIR/servers" "$tmp" || echo "Not needed"

echo 'Removing old version...'
rm -r $INSTALL_DIR 1> /dev/null

echo 'Installing Teeworlds Web Panel...'
git clone https://github.com/CytraL/twp.git "$INSTALL_DIR"

[[ -f "$tmp/twp.service" ]] && cp "$tmp/twp.service" "$INSTALL_DIR"

echo 'Restore database...'
[[ -f "$tmp/twp.db" ]] && cp "$tmp/twp.db" "$INSTALL_DIR"

echo 'Restore servers...'
[[ -d "$tmp/servers" ]] && cp -r "$tmp/servers" "$INSTALL_DIR"

rm -R "$tmp"

chown -R $INSTALL_USER:$INSTALL_USER $INSTALL_DIR

echo 'Installing dependencies...'
pip install -r "$INSTALL_DIR/requirements.txt"

if hash systemctl &> /dev/null;
then
	service twp start
else
	/etc/init.d/twp start
fi

echo -e '\nUpdate complete!\n\n'
