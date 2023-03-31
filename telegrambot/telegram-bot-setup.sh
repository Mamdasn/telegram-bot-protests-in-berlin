read -p "Enter the IP address of your vps: " IP_ADDRESS
read -p "Enter the http api token of your telegram bot: " TG_BOT_TOKEN

echo Installing nginx to setup the portforwarding from ssl connections to flask
sudo apt-get install -y nginx

echo Setting up ssl files
mkdir SSL
cd SSL
openssl req -newkey rsa:2048 -sha256 -nodes -keyout YOURPRIVATE.key -x509 -days 365 -out YOURPUBLIC.pem -subj "/C=US/ST=New York/L=Brooklyn/O=Example Brooklyn Company/CN=$IP_ADDRESS"
SSL_PUBLIC=$(realpath YOURPUBLIC.pem)
SSL_PRIVATE=$(realpath YOURPRIVATE.key)
curl -F "ip_address=$IP_ADDRESS" -F "url=https://$IP_ADDRESS/" -F "certificate=@YOURPUBLIC.pem" https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook
cd ..

echo
#echo Setting up your environmental variables in Dockerfile
#sed -i "s/TG_BOT_TOKEN=\"Run telegram-bot-setup.sh\"/TG_BOT_TOKEN=\"$TG_BOT_TOKEN\"/g" Dockerfile


cat << EOF | sudo tee /etc/nginx/sites-available/portforwarding.txt
server {
  listen 80;
  listen 443 ssl;
  server_name $IP_ADDRESS;
  ssl_certificate $SSL_PUBLIC;
  ssl_certificate_key $SSL_PRIVATE;

  location / {
    proxy_set_header Host \$http_host;
    proxy_redirect off;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Scheme \$scheme;
    proxy_pass http://0.0.0.0:5000/;
    }
}
EOF

sudo systemctl stop nginx
[ -e "/etc/nginx/sites-enabled/portforwarding.txt" ] && 
	sudo rm /etc/nginx/sites-enabled/portforwarding.txt
sudo ln -s /etc/nginx/sites-available/portforwarding.txt /etc/nginx/sites-enabled/portforwarding.txt
sudo systemctl start nginx && sudo systemctl status nginx

[ ! -e "output" ] && mkdir output
echo Done.
