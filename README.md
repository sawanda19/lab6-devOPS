# Модель: Автоматизоване складання розкладу занять — Генетичний алгоритм (5 семестр)
# Автор: Акімов Андрій, група АІ-231

# ЛР5–ЛР6: Flask API + CI/CD Pipeline

## Структура проєкту

```
lab6/
├── api.py                        # Flask API (ЛР5)
├── test_api.py                   # pytest тести (ЛР6)
├── requirements.txt              # залежності
├── Dockerfile                    # контейнеризація
├── README.md
└── .github/
    └── workflows/
        └── ci.yml                # GitHub Actions pipeline
```

## CI/CD Pipeline — етапи

| Етап | Опис |
|------|------|
| ✅ Install dependencies | `pip install -r requirements.txt` |
| ✅ Syntax check | `python -m py_compile api.py` |
| ✅ Run tests (pytest) | `pytest test_api.py -v` |
| ✅ Build Docker image | `docker build -t schedule-optimizer .` |

## Запуск локально

```bash
pip install -r requirements.txt
python api.py
```

## Запуск тестів локально

```bash
pip install pytest
pytest test_api.py -v
```

## Тестовий запит

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000/calculate" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{}'
```
