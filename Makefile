#!/bin/bash
VENV = vp/bin/
PYTHON = $(VENV)python

create_vp: 
	python3 -m venv vp 

activate_vp: 
	$(source vp/bin/activate)

vp_install:
	$(VENV)/pip3 install -r requirements.txt

destroy_vptest: 
	rm -rf vptest/

destroy_vpdev: 
	rm  -rf vpdev/

destroy_vp:
	rm -rf vp/

destroy_all_vp: destroy_vp destroy_vptest destroy_vpdev 

vp: create_vp activate_vp vp_install
#
create_vpdev: 
	python3 -m venv vpdev 

activate_vpdev: 
	$(source vpdev/bin/activate)

vpdev_install:
	$(VPDEV)/pip3 install -r requirements-dev.txt

vpdev: create_vpdev activate_vpdev vpdev_install
#

create_vptest: 
	python3 -m venv vptest 

activate_vptest: 
	$(source vptest/bin/activate)

vptest_install:
	$(VPTEST)/pip3 install -r requirements-test.txt

vptest: create_vptest activate_vptest vptest_install

runserver:
	$(PYTHON) manage.py runserver

runserver-docker:
	$(PYTHON) manage.py runserver 0.0.0.0:8000 --settings djangointegrationhub.live


migrations: 
	$(PYTHON) manage.py makemigrations

migrate: 
	$(PYTHON) manage.py migrate

collectstatic: 
	$(PYTHON) manage.py collectstatic

url-reverse-static: 
	$(PYTHON) manage.py collectstatic_js_reverse

### deploy/docker commands 

SHELL=/bin/bash



# REDIS/CELERY

redis-server-local: 
	redis-server --port 6360

redis-server: 
	redis-server

# CELERY

celery: 
	$(VENV)celery -A config worker 

# ZIP 

rm-old-zip: 
	rm -f package.zip

rm-results: 
	rm -f results.zip
	rm -rf results

rm-artefacts: rm-old-zip rm-results

zip-package: 
	zip -r9g "package.zip" . --exclude "terraform/*"

create-zip-lazy: rm-artefacts cp-env-settings zip-package 
	

create-zip: pre-deploy-handler cp-env-settings zip-package