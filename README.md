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
- http://client-app.vm/adminer?pgsql=127.0.0.1&username=hhcadminuser&db=hhc&ns=public

