COMPOSE = docker compose 
SERVICE = web


up:
	$(COMPOSE) up

up-watch:
	$(COMPOSE) up --watch

up-build:
	$(COMPOSE) up --build

build:
	$(COMPOSE) build --no-cache

up-d:
	$(COMPOSE) up -d

enter:
	$(COMPOSE) exec $(SERVICE) bash

createsuperuser:
	$(COMPOSE) exec $(SERVICE) python manage.py createsuperuser

load_employee:
	$(COMPOSE) exec $(SERVICE) python manage.py populate_employee_table

update_employee:
	$(COMPOSE) exec $(SERVICE) python manage.py update_employee_id

load_employee_social:
	$(COMPOSE) exec $(SERVICE) python manage.py populate_employee_social

update_client_id:
	$(COMPOSE) exec $(SERVICE) python manage.py update_client_id

load_faq_data:
	$(COMPOSE) exec $(SERVICE) python manage.py load_faq_data

pre-commit:
	pre-commit run --all-files

populate-history:
	$(COMPOSE) exec $(SERVICE) python manage.py populate_history --auto

shell:
	$(COMPOSE) exec $(SERVICE) python manage.py shell

scale:
	$(COMPOSE) up --scale $(SERVICE)=3 -d

test:
	$(COMPOSE) exec $(SERVICE) python manage.py test

down:
	$(COMPOSE) down

collectstatic:
	$(COMPOSE) exec $(SERVICE) python manage.py collectstatic

migrate:
	$(COMPOSE) exec $(SERVICE) python manage.py migrate

dbbackup:
	$(COMPOSE) exec $(SERVICE) python manage.py dbbackup

dbrestore:
	$(COMPOSE) exec $(SERVICE) python manage.py dbrestore

migrations:
	$(COMPOSE) exec $(SERVICE) python manage.py makemigrations

showmigrations:
	$(COMPOSE) exec $(SERVICE) python manage.py showmigrations
