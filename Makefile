
build:
	docker-compose build

shell:
	docker-compose exec crawler /bin/bash

logs:
	docker-compose logs -f --tail=30 crawler

up:
	docker-compose up

down:
	docker-compose down