#!/usr/bin/env bash

function usage {
  echo "Usage: ./$(basename $0) [options] target"
  echo "Targets:"
  echo "  dep     install dependencies: apache, mod-wsgi, pip and flask"
  echo "  conf    create apache wsgi configuration"
  echo "  ssl     install ssl variant and modify apache configuration for it"
  echo
  echo "Options:"
  echo "  -h|--help       show this help message"
  echo "  -c|--conf \$path apache configuration file"
  echo
}

# @see http://www.datasciencebytes.com/bytes/2015/02/24/running-a-flask-app-on-aws-ec2/

basedir=$(dirname "$0")
appname=$(basename "$basedir")
appdir=$(realpath "$basedir")
conf=/etc/apache2/sites-enabled/000-default.conf
target=
linkdir=/var/www/html

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -c|--conf)
      conf="$2"
      shift
      ;;
    *)
      break
      ;;
  esac
  shift
done

if [[ $# -gt 1 ]]; then
  echo "Too many arguments!"
  exit 1
elif [[ $# -ne 1 ]]; then
  echo "Missing target!"
  echo
  usage
  exit 1
else
  target="$1"
fi

# actions
case "$target" in
  dep|dependencies)
    # 1. Install dependencies
    sudo apt-get update
    sudo apt-get install apache2
    sudo apt-get install libapache2-mod-wsgi

    sudo apt-get install python-pip
    sudo pip install flask
    ;;

  app)
    # 2. Link in /var/www/html
    sudo ln -sT "$appdir" "/var/www/html/$appname"

    # 3. Enable mod_wsgi
    read wsgi << EOF
WSGIDaemonProcess $appname threads=5
WSGIScriptAlias / /var/www/html/$appname/server.wsgi

<Directory $appname>
    WSGIProcessGroup $appname
    WSGIApplicationGroup %{GLOBAL}
    Order deny,allow
    Allow from all
</Directory>
EOF

    if [[ -f "$conf" ]]; then
      sed -i "DocumentRoot \/var\/www\/html/a $wsgi" "$conf"
    else
      echo "Did not find default site configuration ($conf)"
      echo "You need to add the following to your site configuration (after DocumentRoot):"
      echo
      echo "$wsgi"
      echo
    fi
    ;;

  ssl)

    # @see https://certbot.eff.org/#ubuntuxenial-apache

    echo "Domain to install configuration for:"
    read domain

    conf_ssl=/etc/apache2/sites-enabled/000-default-ssl.conf

    # 1. Install certbot repository
    sudo apt-get install software-properties-common
    sudo add-apt-repository ppa:certbot/certbot
    sudo apt-get update
    sudo apt-get install python-certbot-apache 
    
    # 2. Run certbot for apache
    # this fails because of flask wsgi process
    sudo certbot --apache
    
    # 3. Create SSL configuration
    # @see https://github.com/certbot/certbot/issues/1820
    cp "$conf" "$conf_ssl"
    read ssl_lines << EOF
Include /etc/letsencrypt/options-ssl-apache.conf
SSLCertificateFile /etc/letsencrypt/live/$domain/cert.pem
SSLCertificateKeyFile /etc/letsencrypt/live/$domain/privkey.pem
SSLCertificateChainFile /etc/letsencrypt/live/$domain/chain.pem
EOF
    sed -i 's/<VirtualHost *:80>/<VirtualHost *:443>/' "$conf_ssl"
    sed -i "/</VirtualHost>/i $ssl_lines" "$conf_ssl"
    
    # 4. Load SSL module for Apache
    # @see https://unix.stackexchange.com/questions/31378/apache2-invalid-command-sslengine
    sudo a2enmod ssl
    
    # 5. Restart apache
    sudo apachectl restart
    ;;

esac
