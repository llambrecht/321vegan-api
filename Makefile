.PHONY: install run up stop down initdb migration-create migration-apply migration-down create-admin

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

VENV=.venv
PYTHON=$(VENV)/bin/python3

cmd-exists-%:
	@hash $(*) > /dev/null 2>&1 || \
		(echo "ERROR: '$(*)' must be installed and available on your PATH."; exit 1)

install:  ## Build and run Docker Compose services, Downgrade alambic to base and upgrade to head
	docker compose build --no-cache
	docker compose up -d --force-recreate
	docker exec -it 321veganapi poetry run alembic downgrade base 
	docker exec -it 321veganapi poetry run alembic upgrade head 
	docker exec -it 321veganapi poetry run python -m scripts.create_admin_user

run: ## Build and run Docker Compose services
	docker compose build
	docker compose up

up:  ## Run Docker Compose services
	docker compose up

stop:	## Stop Docker Compose services
	docker compose stop

down:  ## Shutdown Docker Compose services
	docker compose down

initdb: ## Downgrade alambic to base and upgrade to head
	docker exec -it 321veganapi poetry run alembic downgrade base && alembic upgrade head

migration-create: ## Generate alambic new migration
	docker exec -it 321veganapi poetry run alembic revision --autogenerate -m "new migration"

migration-apply: ## Apply alambic new migration
	docker exec -it 321veganapi poetry run alembic upgrade head

migration-down: ## Downgrade alambic last applied migration
	docker exec -it 321veganapi poetry run alembic downgrade -1

create-admin: ## Create the admin user
	docker exec -it 321veganapi poetry run python -m scripts.create_admin_user
