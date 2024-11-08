sudo apt update

# Install Python and PIP

sudo apt-get install python3
sudo apt-get install -y python3-pip

# Install virtualenv, create project dirtectory and virtual environment
# Note virtual environment is separate from project directory
pip3 install virtualenv
mkdir ~/.virtualenvs
cd ~/.virtualenvs
virtualenv env
. ~/.virtualenvs/env/bin/activate
cd ~
mkdir django_project
cd django_project

# Install Redis
sudo apt install redis-server

# Install Django and third party packages
pip install Django
pip install --upgrade django-crispy-forms
pip install humanize
pip install api2pdf
pip install Pillow
pip install python-dotenv
pip install pandas
pip install simple-salesforce
pip install pip-upgrader
pip install djangorestframework
pip install djangorestframework_simplejwt
pip install markdown
pip install django-filter
pip install psycopg2-binary
pip install beautifulsoup4
pip install html5lib
pip install lxml
pip install "celery[redis]"
pip install redis
pip install django-celery-beat
pip install django-celery-results

# Install PostgreSql and create database
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib
sudo su - postgres
psql
CREATE DATABASE hhc;
CREATE USER django WITH PASSWORD 'xxxxxxxxxxxxxxx';
ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hhc TO django;
\q
exit

# {{ COPY DJANGO PROJECT TO PROJECT DIRECTORY }}

# {{ UPDATE LOCAL .ENV FILE IN SETTINGS }}
# {{ Change permissions as appropriate root:www-data 440 }}

# {{ Install Redis/Celery}}


# Install django project and create database tables
python manage.py collectstatic
python manage.py make migrations
python manage.py migrate
python manage.py createsuperuser
