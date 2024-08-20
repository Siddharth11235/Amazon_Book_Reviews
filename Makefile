up:
	docker compose up airflow-init && docker compose up --build -d
down:
	docker compose down --volumes --rmi all && rm -f datagen/offset.txt

sleep:
	sleep 60
restart: down up sleep
