"""
Пересылает дайджест (Markdown-файл из папки digests/) в Telegram.

Запускается GitHub Actions при появлении нового файла в digests/.
Дайджест пишет задача Claude по расписанию; этот скрипт только
переводит Markdown в формат Telegram и отправляет.

Секреты репозитория: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Использование: python send_telegram.py digests/2026-10-27.md [...]
"""

import html
import os
import re
import sys
import time

import requests

TG_LIMIT = 4000


def inline(text: str) -> str:
    """Экранирует HTML и переводит **жирный**, *курсив*, [текст](url) в теги Telegram."""
    links = []

    def keep_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", keep_link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)

    def put_link(m):
        label, url = links[int(m.group(1))]
        return f'<a href="{html.escape(url)}">{html.escape(label, quote=False)}</a>'

    return re.sub(r"\x00(\d+)\x00", put_link, text)


def table_to_pre(rows: list[str]) -> str:
    """Markdown-таблица -> выровненный моноширинный блок."""
    cells = []
    for r in rows:
        r = r.strip().strip("|")
        parts = [re.sub(r"\*\*|__|`", "", c).strip() for c in r.split("|")]
        if all(re.fullmatch(r":?-{2,}:?", p) for p in parts if p):
            continue  # строка-разделитель |---|
        cells.append(parts)
    if not cells:
        return ""
    width = [max(len(row[i]) if i < len(row) else 0 for row in cells)
             for i in range(max(len(r) for r in cells))]
    lines = ["  ".join((row[i] if i < len(row) else "").ljust(width[i])
                       for i in range(len(width))).rstrip() for row in cells]
    return "<pre>" + html.escape("\n".join(lines), quote=False) + "</pre>"


def md_to_tg(md: str) -> str:
    out, table = [], []
    for line in md.splitlines():
        if line.strip().startswith("|"):
            table.append(line)
            continue
        if table:
            out.append(table_to_pre(table))
            table = []
        s = line.rstrip()
        if re.match(r"^\s*-{3,}\s*$", s):
            out.append("")  # горизонтальная линия
        elif m := re.match(r"^#{1,6}\s+(.*)", s):
            out.append(f"<b>{inline(m.group(1))}</b>")
        elif m := re.match(r"^\s*[-*•]\s+(.*)", s):
            out.append(f"• {inline(m.group(1))}")
        else:
            out.append(inline(s))
    if table:
        out.append(table_to_pre(table))
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_message(text: str, limit: int = TG_LIMIT) -> list[str]:
    parts, cur = [], ""
    for block in text.split("\n\n"):
        candidate = f"{cur}\n\n{block}" if cur else block
        if len(candidate) > limit and cur:
            parts.append(cur)
            cur = block
        else:
            cur = candidate
    if cur:
        parts.append(cur)
    return parts


def strip_tags(text: str) -> str:
    text = re.sub(r'<a href="([^"]+)">([^<]*)</a>', r"\2 (\1)", text)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def send(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for part in split_message(text):
        payload = {"chat_id": chat_id, "text": part, "parse_mode": "HTML",
                   "disable_web_page_preview": True}
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            print(f"HTML отклонён: {r.text}; отправляю простым текстом", file=sys.stderr)
            payload = {"chat_id": chat_id, "text": strip_tags(part),
                       "disable_web_page_preview": True}
            requests.post(url, json=payload, timeout=30).raise_for_status()
        time.sleep(1)


def main() -> None:
    files = [f for f in sys.argv[1:] if f.endswith(".md") and os.path.exists(f)]
    if not files:
        print("Нет новых дайджестов для отправки")
        return
    for path in sorted(files):
        with open(path, encoding="utf-8") as fh:
            text = md_to_tg(fh.read())
        if os.environ.get("DRY_RUN") == "1":
            print(text)
        else:
            send(text)
            print(f"Отправлено: {path}")


if __name__ == "__main__":
    main()
