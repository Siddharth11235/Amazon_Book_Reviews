up:
	docker compose up airflow-init && docker compose up --build -d && sleep 60
down:
	docker compose down --volumes --rmi all && rm -f datagen/offset.txt

restart: down up
