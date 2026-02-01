# Publishing to PyPI

## Автоматическая публикация (рекомендуется)

При создании **Release** в GitHub пакет автоматически публикуется на PyPI.

### Шаги

1. **Создайте API-токен на PyPI**
   - Зайдите на [pypi.org](https://pypi.org) → Account Settings → API tokens
   - Create API token (scope: entire account или конкретный проект)

2. **Добавьте токен в GitHub**
   - Repository → Settings → Secrets and variables → Actions
   - New repository secret: `PYPI_API_TOKEN` (значение — ваш токен)

3. **Создайте Release**
   - Releases → Create a new release
   - Tag: `v0.1.3` (соответствует версии в pyproject.toml)
   - Title: `v0.1.3`
   - Publish release

4. **Workflow** `.github/workflows/publish.yml` автоматически:
   - Соберёт пакет
   - Опубликует на PyPI

### При изменении версии

1. Обновите `version` в `pyproject.toml`
2. Обновите `__version__` в `talkie/__init__.py`
3. Закоммитьте и запушьте
4. Создайте новый Release с тегом `vX.Y.Z`

---

## Ручная публикация

```bash
# Установить инструменты
pip install build twine

# Собрать пакет
python -m build

# Загрузить на PyPI (требуется токен)
twine upload dist/*
# Username: __token__
# Password: <ваш PyPI API token>
```
