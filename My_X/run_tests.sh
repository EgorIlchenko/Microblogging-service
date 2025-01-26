#!/bin/bash

set -e

echo "Запуск тестов с покрытием кода..."

pytest --cov=app --cov-report=term-missing

echo "Тесты успешно завершены!"
