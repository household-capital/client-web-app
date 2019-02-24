This document details the initial set-up of a production environment for the webserver for the project. The entry point is a clean Ubuntu 18.04 install. (Refer to Digital Ocean guides for further information.



### SECTION 1 - SERVER SET-UP
Create a non root user *django* in the scripts below.

SSH to the server

```ssh root@your_server_ip```

Create new user, set firewall 
```adduser django
usermod -aG sudo django
ufw allow OpenSSH
ufw enable
```

Copy SSH keys from root (or manually add)
```
rsync --archive --chown=django:django ~/.ssh /home/django
exit
``` 
Check you can SSH with new username
```
ssh django@your_server_ip
```


### SECTION 2 - Set Up Django with Postgres
Install all packages
```
sudo apt update
sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

Create Postgres Database
```
sudo -u postgres psql
CREATE DATABASE django;
CREATE USER django WITH PASSWORD '{{strong-password}}’;
ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET timezone TO 'UTC’;
GRANT ALL PRIVILEGES ON DATABASE django TO django;
\q
```

Install virtual environment and create project directory *django_project*
```
sudo -H pip3 install --upgrade pip
sudo -H pip3 install virtualenv
mkdir ~/django_project
cd ~/django_project
virtualenv env
source env/bin/activate
```

Install Django, Gunicorn, and the psycopg2 PostgreSQL adaptor 
```
pip install django gunicorn psycopg2-binary
```

Install specific project dependencies (refer application documentation)
```
pip install Django
pip install --upgrade django-crispy-forms
pip install humanize
pip install api2pdf
pip install Pillow 
```


### SECTION 3 - Install Django Project
FTP or otherwise copy django files into the project directory
Note: ensure that copy is done with django permissions (and not root).  All directories and files must be owned rwx by django
Replace the relevant settings file  or information (e.g., development.py) with a production.py in the config directory.

This will need to contain:
- the postgreSQL database, username and password from above;
- the setting DEBUG = False.  
- a production SECRET_KEY.  Don’t use a development key and store this key securely.

#####NEVER RUN PRODUCTION WITH DEBUG SET TO TRUE

Example file below:
```
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3059be9d2454b6eeb5a690f02dad4782'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django',
        'USER': 'django',
        'PASSWORD': ‘isfhjiufe84u4ujfif3',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

Complete initial set-up (ensure there are no migrations folders deployed - these should not be saved in VCS)
```
manage.py makemigrations
manage.py migrate
manage.py createsuperuser
manage.py collectstatic
  ```

Check that you can serve the project (or a test project) using the basic python interpreter
This should be a basic test only as there is no webserver or https protection
##### NEVER RUN DJANGO IN PRODUCTION USING THE INTERPRETER OR WITHOUT SSL INSTALLED
```
sudo ufw allow 8000
manage.py runserver 0.0.0.0:8000
```

The project should be now reachable and served. Access via a browser:
```
http://server_domain_or_IP:8000
```

Troubleshoot if required and the remove the firewall rule
```
sudo ufw delete allow 8000
```


### SECTION 4 - Set-up Gunicorn

The last thing we want to do before leaving our virtual environment is test Gunicorn to make sure that it can serve the application. Gunicorn is a service (contained within the virtual environment) which the webserver will pass traffic to.

We can do this by entering our project directory and using gunicorn to load the project's WSGI module:
```
cd ~/django_project
gunicorn --bind 0.0.0.0:8000 config.wsgi
```
We passed Gunicorn a module by specifying the relative directory path to Django's wsgi.py file, which is the entry point to our application, using Python's module syntax. Inside of this file, a function called application is defined, which is used to communicate with the application.

This will start Gunicorn on the same interface that the Django development server was running on. You can go back and test the app again using a browser. If you open the firewall again. CTRL-C to exit the Gunicorn service.

Exit the virtual environment


```
deactivate
```

We have tested that Gunicorn can interact with our Django application We will now implement a more robust way of starting and stopping the application server. To accomplish this, we'll make systemd service and socket files. The Gunicorn socket will be created at boot and will listen for connections. When a connection occurs, systemd will automatically start the Gunicorn process to handle the connection.

Start by creating and opening a systemd socket file for Gunicorn with sudo privileges:

```
sudo nano /etc/systemd/system/gunicorn.socket
```

```
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```
Save and close the file when you are finished.

Next, create and open a systemd service file for Gunicorn with sudo privileges in your text editor. The service filename should match the socket filename with the exception of the extension:
```
sudo nano /etc/systemd/system/gunicorn.service
```
```
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=django
Group=www-data
WorkingDirectory=/home/django/django_project
ExecStart=/home/django/.virtualenvs/env/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```
We specify the full path to the Gunicorn executable, which is installed within our virtual environment. We will bind the process to the Unix socket we created within the /run directory so that the process can communicate with Nginx. We log all data to standard output so that the journald process can collect the Gunicorn logs. We can also specify any optional Gunicorn tweaks here. For example, we specified 3 worker processes in this case

We can now start and enable the Gunicorn socket. This will create the socket file at /run/gunicorn.sock now and at boot. When a connection is made to that socket, systemd will automatically start the gunicorn.service to handle it:
```
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```
Check the status of the process to find out whether it was able to start:

```
sudo systemctl status gunicorn.socket
```
Next, check for the existence of the gunicorn.sock file within the /run directory:

```
file /run/gunicorn.sock
```
If the systemctl status command indicated that an error occurred or if you do not find the gunicorn.sock file in the directory, it's an indication that the Gunicorn socket was not able to be created correctly. Check the Gunicorn socket's logs by typing:

```
sudo journalctl -u gunicorn.socket
```

You can check the status of the service using: 

```
sudo systemctl status gunicorn
```
This wont be active at this stage as it hasn't received any requests.  You can send a connection request using:
```
curl --unix-socket /run/gunicorn.sock localhost
```

### SECTION 5 - Set-up Nginx to pass to Gunicorn

Start by creating and opening a new server block in Nginx's sites-available directory:
```
sudo nano /etc/nginx/sites-available/django_project
```
```
server {
    listen 80;
    server_name householdcapital.app;

    location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            alias /home/django/django_project/static/collected/;
        }
    
        location /media/ {
            alias /home/django/django_project/static/media/;
        }
    
        location / {
            include proxy_params;
            proxy_pass http://unix:/run/gunicorn.sock;
        }
    }

```
Save and close the file when you are finished. Now, we can enable the file by linking it to the sites-enabled directory:
```
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
```

Test your Nginx configuration for syntax errors by typing:
```
sudo nginx -t
```
If no errors are reported, go ahead and restart Nginx and add a firewall rule:
```
sudo systemctl restart nginx
sudo ufw delete allow 8000
sudo ufw allow 'Nginx Full'
```

You should now be able to go to the server's domain or IP address to view the application.

##### You should never run the application without SSL

### Step 6 - SSL Set-up

Set-up SSL on ubuntu depending upon the source/type of the certificate. This will typically involve keys and certificates being saved to /etc/ssl. 
Not described here.

Once the certificate is installed, the NGINX Configuration file must be updated to use SSL

```
sudo nano /etc/nginx/sites-available/django_project
```

```
server {
    listen 80;
    server_name householdcapital.app;
    rewrite ^/(.*) https://householdcapital.app/$1 permanent;
}
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/householdcapital.app.chained.crt;
    ssl_certificate_key /etc/ssl/private/householdcapital.app.key;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH';

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias /home/django/django_project/static/collected/;
    }

    location /media/ {
        alias /home/django/django_project/static/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

These additional settings force any http request to be redirected to https and reference the relevant locations of the keys and certificates.

Test your Nginx configuration for syntax errors by typing:
```
sudo nginx -t
```

You should now be able to go to the server's domain or IP address to view the application securely over https


### Website Changes
Restart Gunicorn following any update:
```
sudo systemctl restart gunicorn
```

### Log Locations
- Nginx process logs by typing: sudo journalctl -u nginx
- Nginx access logs by typing: sudo less /var/log/nginx/access.log
- Nginx error logs by typing: sudo less /var/log/nginx/error.log
- Gunicorn application logs by typing: sudo journalctl -u gunicorn
- Gunicorn socket logs by typing: sudo journalctl -u gunicorn.socket