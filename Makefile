bootstrap:
	@echo "Bootstrapping project..."
	bash scripts/bootstrap.sh

up:
	@echo "Starting all services..."
	# docker compose -f infra/docker-compose.yml --env-file .env up -d

down:
	@echo "Stopping all services..."
	# docker compose -f infra/docker-compose.yml down

logs:
	# docker compose -f infra/docker-compose.yml logs
