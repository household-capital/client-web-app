# client-web-app

## Dev env getting started

```bash
cp config/settings/.env-deploy .env
# add details
vagrant up
vagrant ssh
python manage.py createsuperuser
```

## Links
- http://client-app.vm/hhcadmin
- http://client-app.vm/landing/dashboard
- http://client-app.vm/adminer?pgsql=127.0.0.1 username=hhcadminuser&db=hhc&ns=public


## LOCAL SETUP 
```
    Ensure Virtual Python is built
    make vp 

    Setup .env file to your personal config

    The next steps require 3 concurrent terminals 
    Terminal 1: make runserver 
    Terminal 2: make redis-server-local
    Terminal 3: make celery 

    Celery command spins up celery and celery beat. 
```

