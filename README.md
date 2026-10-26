# Ежедневный дайджест → Telegram

Как это работает:

1. Каждое утро задача Claude «Утренний дайджест» (на серверах Claude) собирает дайджест
   и сохраняет его файлом `digests/ГГГГ-ММ-ДД.md` в этот репозиторий.
2. Появление файла запускает GitHub Actions (`.github/workflows/send.yml`),
   который переводит текст в формат Telegram и отправляет в бот.

Всё бесплатно: Claude — в рамках подписки, GitHub Actions — бесплатный лимит
(отправка занимает ~20 секунд в день).

## Настройка Telegram (один раз)

1. В Telegram: **@BotFather** → `/newbot` → имя → скопируйте **токен**.
2. Откройте своего бота и нажмите **Start**.
3. Узнайте свой **chat_id** у **@userinfobot** (число в поле `Id`).
4. В этом репозитории: **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` — токен бота
   - `TELEGRAM_CHAT_ID` — ваш chat_id

## Повторная отправка

**Actions → Send digest to Telegram → Run workflow** и укажите путь к файлу,
например `digests/2026-10-27.md`.

Архив всех дайджестов лежит в папке `digests/`.
