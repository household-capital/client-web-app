# use some sensible default shell settings
SHELL := /bin/bash
.ONESHELL:
.SILENT:
.DEFAULT_GOAL := help

RED = '\033[1;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# local variables
HHC_FUNCTION = client
HHC_APPLICATION = web-app

# default variables
HHC_ENVIRONMENT ?= devel
HHC_INSTANCE ?= master
HHC_FULL_NAME = $(HHC_FUNCTION)-$(HHC_APPLICATION)-$(HHC_INSTANCE)

# Devel docker repository
HHC_DOCKER_REPO_ID ?= 767894820823
HHC_DOCKER_REPO = $(HHC_DOCKER_REPO_ID).dkr.ecr.ap-southeast-2.amazonaws.com

# available options
OPT_ENVIRONMENT = ^(devel|stage|prod)$$

# git variables
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_HASH := $(shell git rev-parse --short=8 HEAD)

# current python image
export HHC_IMAGE=$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-$(GIT_HASH)

# terraform configuration
TF_ARTIFACT = ./$(HHC_FULL_NAME).tfplan
TF_VARS := -var 'function=$(HHC_FUNCTION)' \
           -var 'application=$(HHC_APPLICATION)' \
		   -var 'instance=$(HHC_INSTANCE)' \
	       -var-file=./env-vars/$(HHC_ENVIRONMENT).tfvars
TF_OUTPUT = ./terraform/$(HHC_FULL_NAME).json
TF_OUTPUT_APP_NAME = $(shell cat $(TF_OUTPUT) | jq -r ".app_name.value")
TF_OUTPUT_APP_VER = $(shell cat $(TF_OUTPUT) | jq -r ".app_ver.value")
TF_OUTPUT_ENV_NAME = $(shell cat $(TF_OUTPUT) | jq -r ".env_name.value")

# docker-compose calls
PYTHON = docker-compose run python
TERRAFORM = docker-compose run terraform
AWSCLI = docker-compose run awscli


##@ Main targets
build: pyimage pypublish create-zip ## Package and publish code
deploy: tfformat tfvalidate tfplan tfapply ebupdate ## Format, validate, plan, and apply terraform
destroy: tfdestroy ## Destroy environment


VENV = vp/bin
VPYTHON = $(VENV)/python

AWS_PROFILE ?= devel
# ideally we would export this to make the tfinit use the selected account too - BUT the S3 bucket we use for
# state storage isn't accessible by any AWS account but the root one yet. We need to tidy that up.
# export AWS_PROFILE

create_vp: 
	python3 -m venv vp
	$(VENV)/pip3 install --upgrade pip

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

create_vpdev: 
	python3 -m venv vpdev 

activate_vpdev: 
	$(source vpdev/bin/activate)

vpdev_install:
	$(VPDEV)/pip3 install -r requirements-dev.txt

vpdev: create_vpdev activate_vpdev vpdev_install

create_vptest: 
	python3 -m venv vptest 

activate_vptest: 
	$(source vptest/bin/activate)

vptest_install:
	$(VPTEST)/pip3 install -r requirements-test.txt

vptest: create_vptest activate_vptest vptest_install

runserver:
	$(VPYTHON) manage.py runserver

runserver-docker:
	$(VPYTHON) manage.py runserver 0.0.0.0:8000 --settings djangointegrationhub.live


migrations: 
	$(VPYTHON) manage.py makemigrations

migrate: 
	$(VPYTHON) manage.py migrate

collectstatic: 
	$(VPYTHON) manage.py collectstatic

url-reverse-static: 
	$(VPYTHON) manage.py collectstatic_js_reverse


# REDIS/CELERY
redis-server-local: 
	redis-server --port 6360

redis-server: 
	redis-server

# CELERY
celery: 
	$(VENV)/celery -A config worker -l debug --beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=info


##@ Zip targets
.PHONY: rm-old-zip
rm-old-zip: ## Remove old package
	echo -e $(CYAN)Removing old package$(NC)
	$(PYTHON) rm -f package.zip

.PHONY: zip-package
zip-package: ## Create package
	echo -e $(CYAN)Creating package$(NC)
	$(PYTHON) zip -r9g "package.zip" . --exclude "terraform/*" ".git/*" "vp/*" ".buildkite/*"

create-zip: rm-old-zip zip-package


# SNAPSHOT 
rds-snapshot: 
	sh rds_snapshot.sh $(HHC_ENVIRONMENT)

apply-deploy-with-snapshot: rds-snapshot create-zip tfapply ebupdate


shell_plus: 
	$(VPYTHON) manage.py shell_plus --print-sql


##@ Authorisation targets
.PHONY: authconfig
authconfig: ## Authorisation configuration
	echo -e $(CYAN)Authorisation configuration$(NC)
	$(AWSCLI) configure sso

.PHONY: auth
auth: ## Authorisation into default profile
	echo -e $(CYAN)Authorisation into default profile$(NC)
	$(AWSCLI) sso login


##@ Build targets
.PHONY: pyimage
pyimage: ## Create Python docker image
	echo -e $(CYAN)Creating Python docker image$(NC)
	docker build \
		-t "$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-latest" \
		-t "$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-${GIT_BRANCH}" \
		-t "$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-${GIT_HASH}" \
		-t "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-latest" \
		-t "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-$(GIT_BRANCH)" \
		-t "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-$(GIT_HASH)" \
		./

.PHONY: pypublish
pypublish: ## Publish Python docker image
	echo -e $(CYAN)Publishing Python docker image$(NC)
	# Hack start
	# There seems to be a replication delay between when an ECR password is issued and when it can be used.
	# Added delay between two identical calls to login into ECR. The first always fails and the second succeeds.
	$(AWSCLI) ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin $(HHC_DOCKER_REPO)
	sleep 5
	# Hack end
	$(AWSCLI) ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin $(HHC_DOCKER_REPO)
	docker push "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-latest"
	docker push "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-$(GIT_BRANCH)"
	docker push "$(HHC_DOCKER_REPO)/$(HHC_FUNCTION)-$(HHC_APPLICATION):$(HHC_INSTANCE)-$(GIT_HASH)"


##@ Terraform targets
.PHONY: tfformat
tfformat: _validate  ## Format terraform
	echo -e $(CYAN)Formating terraform$(NC)
	$(TERRAFORM) fmt -write=true -recursive

.PHONY: tfvalidate
tfvalidate: _validate ## Validate terraform syntax
	echo -e $(CYAN)Validating terraform$(NC)
	$(TERRAFORM) init -input=false -backend=false
	$(TERRAFORM) validate

.PHONY: tfplan
tfplan: _tfinit ## Generate terraform plan
	echo -e $(CYAN)Planning terraform$(NC)
	$(TERRAFORM) plan $(TF_VARS) -out $(TF_ARTIFACT)

.PHONY: tfapply
tfapply: _validate ## Apply terraform plan
	echo -e $(CYAN)Applying terraform$(NC)
	$(TERRAFORM) apply $(TF_ARTIFACT) && \
	$(TERRAFORM) output -no-color -json > $(TF_OUTPUT)
	
.PHONY: ebupdate
ebupdate: ## Update elasticbeanstalk
	echo -e $(CYAN)Updating elasticbeanstalk$(NC)
	$(AWSCLI) elasticbeanstalk update-environment \
		--application-name $(TF_OUTPUT_APP_NAME) \
		--version-label $(TF_OUTPUT_APP_VER) \
		--environment-name $(TF_OUTPUT_ENV_NAME)

.PHONY: tfdestroy
tfdestroy: _tfinit ## Destroy infrastructure
	echo -e $(RED)Destroying terraform$(NC)
	$(TERRAFORM) destroy -auto-approve $(TF_VARS)

.PHONY: tfrefresh
tfrefresh: _tfinit ## Refresh terraform state
	echo -e $(CYAN)Refreshing terraform$(NC)
	$(TERRAFORM) refresh $(TF_VARS)


##@ Shell targets
.PHONY: awscli
awscli: ## Shell into awscli
	echo -e $(CYAN)Shelling into awscli$(NC)
	docker-compose run --entrypoint=bash awscli

.PHONY: terraform
terraform: ## Shell into terraform
	echo -e $(CYAN)Shelling into terraform$(NC)
	docker-compose run --entrypoint=ash terraform

.PHONY: pyshell
pyshell: ## Shell into Python image
	echo -e $(CYAN)Shelling into Python image$(NC)
	docker-compose run --entrypoint=bash python


##@ Misc targets
.PHONY: help
help: ## Display this help
	awk \
	  'BEGIN { \
	    FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n" \
	  } /^[a-zA-Z_-]+:.*?##/ { \
	    printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 \
	  } /^##@/ { \
	    printf "\n\033[1m%s\033[0m\n", substr($$0, 5) \
	  } ' $(MAKEFILE_LIST)


##@ Helpers
.PHONY: _tfinit
_tfinit: _validate _clean ## Initialise terraform state
	echo -e $(CYAN)Initialising terraform$(NC)
	$(TERRAFORM) init -input=false \
		-backend-config="key=$(HHC_FUNCTION)/$(HHC_APPLICATION)/$(HHC_ENVIRONMENT)/$(HHC_INSTANCE)/terraform.tfstate" \
		-backend-config="bucket=hhc-terraform-tech-account-infra-$(HHC_ENVIRONMENT)" \
		-backend-config="dynamodb_table=hhc-terraform-tech-account-infra-$(HHC_ENVIRONMENT)" \
		-reconfigure

.PHONY: _clean
_clean: ## Remove terraform directory and docker networks
	echo -e $(CYAN)Removing .terraform directory and docker networks$(NC)
	docker-compose run --entrypoint="rm -rf .terraform" terraform
	docker-compose down --remove-orphans 2>/dev/null

.PHONY: _validate
_validate: ## Validate environment variables
	[[ "$(HHC_ENVIRONMENT)" =~ $(OPT_ENVIRONMENT) ]] || (echo "$(HHC_ENVIRONMENT) is not a valid option" && exit 1)
