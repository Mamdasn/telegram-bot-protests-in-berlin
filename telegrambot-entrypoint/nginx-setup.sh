#!/bin/sh

echo Setting up the nginx configuration file
cat > /etc/nginx/nginx.conf <<EOF
events {
    worker_connections 1000;
}
http {
    server {
	listen 443 ssl;
        server_name localhost;
        ssl_certificate /etc/nginx/cert.pem;
        ssl_certificate_key /etc/nginx/cert.key;
        
        location / {
WHITE_LISTED_IPS
		deny all;
    		proxy_redirect off;
        	proxy_pass http://0.0.0.0:5000;
		proxy_set_header Host \\\$http_host;
    		proxy_set_header X-Scheme \\\$scheme;
    		proxy_set_header X-Real-IP \\\$remote_addr;
    		proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        }
    }
}
EOF


echo Copying the ssl file to the /etc/nginx dir
SSL_PUBLIC=/app/SSLFILES/YOURPUBLIC.pem
SSL_PRIVATE=/app/SSLFILES/YOURPRIVATE.key
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
