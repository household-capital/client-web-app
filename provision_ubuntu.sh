WEBROOT=/vagrant

# Install Python and PIP
sudo apt-get install -y python3 python3-pip virtualenv postgresql postgresql-contrib libpq-dev apache2 libapache2-mod-wsgi-py3

# Install virtualenv, create virtual environment
# Note virtual environment is separate from project directory
mkdir ~/.virtualenvs
cd ~/.virtualenvs
virtualenv -p python3 env
. ~/.virtualenvs/env/bin/activate

# Install Django and third party packages
pip install django humanize api2pdf django-crispy-forms psycopg2-binary pillow

cd $WEBROOT

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

# Install django project and create database tables
python manage.py collectstatic
python manage.py migrate

# Doesnt work in headless mode, wont accept input from cli
# python manage.py createsuperuser

# using WCGI via Apache
# python manage.py runserver
