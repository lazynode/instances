#!/bin/sh
if [ -z "$(ls /etc/letsencrypt)" ]
then
	echo branch new
	certbot certonly --standalone --agree-tos --email email@example.com --no-eff-email --domain domain.example.com
fi;
echo renewing ...
while :
do
	certbot renew
	sleep 36000
done
