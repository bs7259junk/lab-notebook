.PHONY: up down reset logs shell-backend shell-db

up:
	bash setup.sh

down:
	docker compose down

reset:
	docker compose down -v
	bash setup.sh

logs:
	docker compose logs -f

shell-backend:
	docker exec -it eln_backend bash

shell-db:
	docker exec -it eln_db psql -U elnuser -d elndb
