#!/bin/sh

echo Copying the ssl file to the /etc/nginx dir
SSL_PUBLIC=$(realpath SSLFILES/YOURPUBLIC.pem)
SSL_PRIVATE=$(realpath SSLFILES/YOURPRIVATE.key)
cp "$SSL_PUBLIC" /etc/nginx/cert.pem
cp "$SSL_PRIVATE" /etc/nginx/cert.key

echo
echo Downloading a list of telegram server ips to make a whitelist for nginx...
IPLIST=$(curl -s https://core.telegram.org/resources/cidr.txt)
WHITE_LISTED_IPS=$(echo "$IPLIST" | awk '{print "		allow " $0";"}')
# Escape forward slashes and replace newlines with '\n' to prepare the data for sed
WHITE_LISTED_IPS_ESCAPED=$(echo "$WHITE_LISTED_IPS" | sed 's#/#\\/#g' | awk '{printf "%s\\n", $0}')

echo
echo Setting up the white listed IPs in the nginx configuration file
sed -i "s#WHITE_LISTED_IPS#$WHITE_LISTED_IPS_ESCAPED#g" /etc/nginx/nginx.conf
echo Done.

