#!/bin/bash
VENV = vp/bin/
PYTHON = $(VENV)python

ENV ?= dev
BACKEND_FILE ?= backends/$(ENV).hcl
CONFIG_FILE ?= env-vars/$(ENV).tfvars

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
	$(VENV)celery -A config worker -l debug --beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=info

# ZIP 

rm-old-zip: 
	rm -f package.zip

rm-static:
	cd static && find . -type d -not -path "*uncollected*" -not -path "\." | xargs rm -rf

rm-artefacts: rm-old-zip

zip-package: 
	zip -r9g "package.zip" . --exclude "terraform/*" ".git/*"

create-zip-lazy: zip-package 
	
pre-deploy-handler: destroy_all_vp rm-static rm-artefacts
 
create-zip: pre-deploy-handler zip-package


tfinit:
	cd terraform && terraform init -backend-config=$(BACKEND_FILE)

apply: tfinit
	cd terraform && terraform apply -var-file=$(CONFIG_FILE)

apply_hard: tfinitf
	cd terraform && echo "yes" | terraform apply -var-file=$(CONFIG_FILE)

destroy:
	cd terraform && terraform destroy -var-file=$(CONFIG_FILE)

destroy_hard:
	cd terraform && echo "yes" | terraform destroy -var-file=$(CONFIG_FILE)

apply-deploy: create-zip apply