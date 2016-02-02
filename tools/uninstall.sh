#!/bin/bash

if [[ "$UID" -ne "0" ]];then
	echo 'You must be root to uninstall Teeworlds Web Panel!'
	exit 1
fi

read -r -p "Do you want uninstall TWP? This goes to remove all tw servers data! [Y/n]: " response
if [[ $response =~ [nN] ]]; then
	exit 0
fi

/etc/init.d/twp stop
rm -R /srv/twp
update-rc.d -f twp remove

echo 'Teeworlds Web Panel uninstalled successfully!'
echo -e "Report bugs: https://github.com/CytraL/twp/issues\n\n"
