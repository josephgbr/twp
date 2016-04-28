#!/bin/bash
echo '████████╗  ██╗    ██╗  ██████╗ '
echo '╚══██╔══╝  ██║    ██║  ██╔══██╗'
echo '   ██║     ██║ █╗ ██║  ██████╔╝'
echo '   ██║     ██║███╗██║  ██╔═══╝ '
echo '   ██║     ╚███╔███╔╝  ██║     '
echo '   ╚═╝      ╚══╝╚══╝   ╚═╝     '
echo '               Teeworlds Web Panel Automatic installer'
echo -e "\n"

INSTALL_DIR='/srv/twp'

if [[ -n $SUDO_USER ]]; then
	INSTALL_USER=$SUDO_USER
elif [[ -n $1 ]]; then
	INSTALL_USER=$1
fi

if [[ -z $INSTALL_USER ]]; then
	echo -e "Error, can't read user installation!"
	exit 1
fi

if [[ "$UID" -ne 0 ]]; then
	echo 'You must be root to install Teeworlds Web Panel!'
	exit 1
fi

if [[ "$INSTALL_USER" == "root" ]]; then
	echo "Error, install for 'root' user it's a security issue... change user and try again."
	exit 1
fi

if [[ -d "$INSTALL_DIR" ]];then
	echo "You already have Teeworlds Web Panel installed. You'll need to remove $INSTALL_DIR if you want to install"
	exit 1
fi

read -r -p "Do you want install TWP using '$INSTALL_USER' user? [Y/n]: " response
if [[ $response =~ [nN] ]]; then
	exit 0
fi

### CHECK PACKAGE MANAGER
hash apt-get &> /dev/null || {
	PKG_MANGER = "apt-get"
}
hash yum &> /dev/null || {
	PKG_MANGER = "yum"
}
hash pacman &> /dev/null || {
	PKG_MANGER = "pacman"
}
hash emerge &> /dev/null || {
	PKG_MANGER = "emerge"
}


### INSTALL TWP
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

echo 'Cloning Teeworlds Web Panel...'
hash git &> /dev/null || {
	echo '+ Installing Git'
	apt-get install -y git 1> /dev/null
}

git clone https://github.com/CytraL/twp.git "$INSTALL_DIR"
chown -R "$INSTALL_USER":"$INSTALL_USER" "$INSTALL_DIR"

echo 'Installing dependencies...'
pip uninstall -y pillow &> /dev/null
pip install -r "$INSTALL_DIR/requirements.txt"

echo -e '\nInstallation complete!\n\n'

### DAEMON
if hash systemctl &> /dev/null;
then
	echo -e 'Writing twp.service... '
	
	cat > "$INSTALL_DIR/twp.service" <<EOF
[Unit]
Description=Teeworlds Web Panel
After=network.target

[Service]
User=$INSTALL_USER
Type=simple
ExecStart=/usr/bin/python2 "$INSTALL_DIR/twp.py"
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF
	
	systemctl enable "$INSTALL_DIR/twp.service"
	echo -e 'Done\n'
	service twp start
else
	echo -e 'Writing /etc/init.d/twp... '
	
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
	update-rc.d twp defaults 1> /dev/null
	echo -e 'Done\n'
	/etc/init.d/twp start
fi


### END
echo 'Connect you on http://your-ip-address:8000/ (Example: http://localhost:8000)'
echo 'User: admin'
echo 'Password: admin'
echo -e "*** DON'T FORGET CHANGE DEFAULT ADMIN PASSWORD!!! ***\n\n"
