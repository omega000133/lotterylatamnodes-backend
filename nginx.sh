# Update and install nginx
sudo apt update
sudo apt install -y nginx

sudo systemctl stop nginx

cd nginx/site-available
sudo cp -f default /etc/nginx/site-available

sudo systemctl start nginx