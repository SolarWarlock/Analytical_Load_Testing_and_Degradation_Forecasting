# Скрипт посекундного сбора аппаратных метрик контейнера
Write-Host "Запуск сбора метрик Docker для контейнера fastapi-backend..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "load_testing\raw_data" | Out-Null

while ($true) {
    docker stats fastapi-backend --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" | Out-File -Append -Encoding ascii "load_testing\raw_data\docker_metrics.csv"
    Start-Sleep -Seconds 1
}
