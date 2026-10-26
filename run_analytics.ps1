# Скрипт выполнения полного пайплайна машинного обучения и аналитики
$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\analytics"

Write-Host "🧠 Шаг 1/3: Подготовка мастер-датасета..." -ForegroundColor Cyan
py -3.13 02_prepare_dataset.py

Write-Host "`n📊 Шаг 2/3: Генерация признакового пространства (Feature Engineering)..." -ForegroundColor Cyan
py -3.13 04_feature_engineering.py

Write-Host "`n🎯 Шаг 3/3: Обучение Random Forest и калибровка порога Юдена..." -ForegroundColor Cyan
$env:PYTHONIOENCODING="utf-8"
py -3.13 06_train_classifier.py

Write-Host "`n✅ Весь аналитический конвейер успешно выполнен!" -ForegroundColor Green
