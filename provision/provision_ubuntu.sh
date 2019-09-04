export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
sudo locale-gen "en_US.UTF-8"

# Install Python and PIP
sudo apt-get install -y \
adminer \
apache2 \
libapache2-mod-wsgi-py3 \
libpq-dev \
postgresql \
postgresql-contrib \
python3 \
python3-pip \
virtualenv

# Install virtualenv, create virtual environment
# Note virtual environment is separate from project directory
mkdir ~/.virtualenvs
cd ~/.virtualenvs
virtualenv -p python3 env

sudo mkdir /usr/share/adminer
sudo wget -q "https://www.adminer.org/latest.php" -O /usr/share/adminer/latest.php
sudo ln -fs /usr/share/adminer/latest.php /usr/share/adminer/adminer.php
echo "Alias /adminer /usr/share/adminer/adminer.php" | sudo tee /usr/share/adminer/apache.conf
sudo ln -fs /usr/share/adminer/apache.conf /etc/apache2/conf-available/adminer.conf
sudo a2enconf adminer.conf

sudo ln -s /vagrant/provision/vagrant.conf /etc/apache2/sites-available/
sudo a2ensite vagrant
sudo a2dissite 000-default.conf
sudo systemctl reload apache2

# Install PostgreSql and create database
sudo su - postgres
psql
CREATE DATABASE hhc;
CREATE USER hhcadminuser WITH PASSWORD 'Household01';
ALTER ROLE hhcadminuser SET client_encoding TO 'utf8';
ALTER ROLE hhcadminuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE hhcadminuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hhc TO hhcadminuser;
\q
exit

cd /vagrant
. ~/.virtualenvs/env/bin/activate

# Install Django and third party packages
pip install -r requirements.txt

# Install django project and create database tables
python manage.py migrate
python manage.py collectstatic --noinput

# Doesnt work in headless mode, wont accept input from cli
# python manage.py createsuperuser

# using WCGI via Apache, not required on this vagrant
# python manage.py runserver
sudo systemctl reload apache2
