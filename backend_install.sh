#!/bin/bash

# Update and install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib libpq-dev python3-dev

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create a PostgreSQL role and database
sudo -u postgres psql <<EOF
CREATE USER postgres WITH PASSWORD '123456';
ALTER USER postgres WITH PASSWORD '123456';
CREATE DATABASE db_loteria_latam_nodes;
GRANT ALL PRIVILEGES ON DATABASE myproject TO postgres;
EOF

# Install Python virtual environment tools if not already installed
sudo apt install -y python3-venv

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install Django and psycopg2
pip install -r requirements/dev.txt

# Create .env
echo "DB_USER=postgres" > .env
echo "DB_HOST=localhost" >> .env
echo "DB_PASSWORD=123456" >> .env
echo "DB_NAME=db_loteria_latam_nodes" >> .env

# Migrate the database
python manage.py migrate

# Create super user
printf "\033[34m Write username for super user: \033[0m" && read SUPER_USERNAME
printf "\033[34m Write email for super user: \033[0m" && read SUPER_EMAIL
printf "\033[34m Write password for super user: \033[0m" && read SUPER_PASSWORD

echo -e "\t username: $SUPER_USERNAME \n\t email: $SUPER_EMAIL \n\t password: *********"

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$SUPER_USERNAME', '$SUPER_EMAIL', '$SUPER_PASSWORD')" | python manage.py shell

# Message to indicate end of setup
echo "Backend setup was finished"