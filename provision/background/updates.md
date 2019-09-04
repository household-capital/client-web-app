### Application updates

Stop the Gunicorn service

```
 sudo service gunicorn stop
```

#####1. Update Django files
But do not update:
- application migrations folders 
- static/media folder
- config/settings/development.py (production.py is used in production)

#####2. Update any dependencies
For example via PIP install

#####3. Update the Django Project
```
source ~/.virtualenvs/env/bin/activate
cd ~/django_project
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

#####4. Check for Load errors
You can check for any start-up errors by running it under local server or gunicorn:
```
python manage.py runserver
```
This can't be accessed by the browser but will report any load errors.

#####5. Restart the Gunicorn service
```
 sudo service gunicorn start
```


#####Common deployment issues
- model migrations - these may need to be faked or changes to tables made in psql
- additional dependencies that have not been installed