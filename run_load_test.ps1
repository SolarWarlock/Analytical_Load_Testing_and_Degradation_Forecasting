# Скрипт запуска генератора нагрузки Locust
Write-Host "Запуск 15-минутного нагрузочного тестирования Locust..." -ForegroundColor Green
locust -f load_testing/locustfile.py --headless -u 200 -r 10 --run-time 15m --host http://localhost:8000 --csv load_testing/raw_data/experiment_stats
