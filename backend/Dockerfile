# Используем легковесный официальный образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код бэкенда
COPY ./app ./app

# Запускаем Uvicorn сервер
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]