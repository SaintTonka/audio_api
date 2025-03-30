Перед запуском скопируйте .env.example в .env с вашими настройками

# Запустите сервисы
docker compose up -d --build

# Примените миграции БД
docker compose exec alembic alembic upgrade head

## Полезные команды

# Проверить работу API (ожидаемый вывод {"status":"ok"})
curl http://localhost:8000/health

# Документация API (swagger)
curl http://localhost:8000/api/docs  