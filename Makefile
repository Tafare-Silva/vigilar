.PHONY: help install run migrate makemigrations shell test lint format celery

help:
	@echo "Comandos disponíveis:"
	@echo "  make install         Instala dependências"
	@echo "  make run             Inicia o servidor de desenvolvimento"
	@echo "  make migrate         Executa as migrações"
	@echo "  make makemigrations  Cria novas migrações"
	@echo "  make shell           Abre o shell do Django"
	@echo "  make test            Executa os testes"
	@echo "  make lint            Verifica o código com ruff"
	@echo "  make format          Formata o código com ruff"
	@echo "  make celery          Inicia o Celery worker"
	@echo "  make celery-beat     Inicia o Celery Beat (agendador)"

install:
	pip install -r requirements-dev.txt

run:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus --ipython

test:
	pytest --cov=apps --cov-report=html -v

lint:
	ruff check apps/ config/

format:
	ruff format apps/ config/

celery:
	celery -A config worker -l info

celery-beat:
	celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

superuser:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic --noinput
