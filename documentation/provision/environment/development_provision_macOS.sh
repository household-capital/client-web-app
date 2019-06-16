# Install Brew, Python (including PIP)
 xcode-select --install
 /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
 brew install python3

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

# Install PostgreSql and create database
brew install postgresql
pip install psycopg2-binary
mkdir -p ~/Library/LaunchAgents
ln -sfv /usr/local/opt/postgresql/*.plist ~/Library/LaunchAgents
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist
createdb
psql
CREATE DATABASE hhc;
CREATE USER hhcadminuser WITH PASSWORD 'Household01';
ALTER ROLE hhcadminuser SET client_encoding TO 'utf8';
ALTER ROLE hhcadminuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE hhcadminuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hhc TO hhcadminuser;
\q

# {{ COPY DJANGO PROJECT TO PROJECT DIRECTORY }}

# {{ UPDATE LOCAL .ENV FILE IN SETTINGS }}

# Install django project and create database tables
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
