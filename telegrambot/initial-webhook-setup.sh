#!/bin/sh

PORTSSL=443

[ -z $IP_ADDRESS ] &&
	echo set the IP_ADDRESS by running: export IP_ADDRESS={IP_ADDRESS}. &&
		return
[ -z $TG_BOT_TOKEN ] &&
	echo set the TG_BOT_TOKEN by running: export TG_BOT_TOKEN={TG_BOT_TOKEN}. &&
		return

echo IP_ADDRESS: $IP_ADDRESS
echo TG_BOT_TOKEN: $TG_BOT_TOKEN

echo Setting up ssl files
mkdir -p /app/SSLFILES
cd /app/SSLFILES
openssl req -newkey rsa:4096 -sha256 -nodes -keyout YOURPRIVATE.key -x509 -days 365 -out YOURPUBLIC.pem -subj "/C=US/ST=New York/L=Brooklyn/O=Example Brooklyn Company/CN=$IP_ADDRESS"
SSL_PUBLIC=$(realpath YOURPUBLIC.pem)
SSL_PRIVATE=$(realpath YOURPRIVATE.key)
echo SSL_PUBLIC: $SSL_PUBLIC
echo SSL_PRIVATE: $SSL_PRIVATE

curl -F "ip_address=$IP_ADDRESS" -F "url=https://$IP_ADDRESS:$PORTSSL/" -F "certificate=@YOURPUBLIC.pem" "https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook"

echo
echo Continuing to the next stage
