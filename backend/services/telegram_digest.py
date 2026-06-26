import json
import os
import sys
import re
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

if getattr(sys, "frozen", False):
    DATA_DIR = os.path.join(os.path.dirname(sys.executable), "data")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

DB_FILE = os.path.join(DATA_DIR, "telegram_digest_db.json")
EMAIL_BODIES_DIR = os.path.join(DATA_DIR, "email_bodies")


def _ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(EMAIL_BODIES_DIR, exist_ok=True)


def load_db() -> dict:
    _ensure_dirs()
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            db.setdefault("last_update_id", 0)
            db.setdefault("processed_ids", [])
            db.setdefault("total_processed", 0)
            db.setdefault("total_emails", 0)
            db.setdefault("history", [])
            return db
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "last_update_id": 0,
        "processed_ids": [],
        "total_processed": 0,
        "total_emails": 0,
        "history": [],
    }


def save_db(db: dict):
    _ensure_dirs()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def extract_urls(text: str) -> list[str]:
    pattern = r'https?://[^\s<>"\')\]]+'
    raw = re.findall(pattern, text)
    seen = set()
    urls = []
    for u in raw:
        u = u.rstrip(".,;:!?")
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def fetch_url_content(url: str) -> str:
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            resp.raise_for_status()
            html = resp.text
    except Exception:
        return ""

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()

    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()

    main_content = ""
    for selector in ["article", "main", "[role='main']"]:
        el = soup.select_one(selector)
        if el:
            main_content = el.get_text(separator="\n", strip=True)
            break

    if not main_content:
        body = soup.find("body")
        if body:
            main_content = body.get_text(separator="\n", strip=True)

    parts = [p for p in [title, meta_desc, main_content] if p]
    text = "\n\n".join(parts)
    return text[:5000]


def generate_digest(content_text: str, message_text: str, provider_index: int, model: str) -> dict:
    from openai import OpenAI
    from backend.services.config import load_config

    config = load_config()
    providers = config.get("providers", [])
    if 0 <= provider_index < len(providers):
        provider = providers[provider_index]
    else:
        provider = providers[0] if providers else {}

    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "https://api.openai.com/v1").rstrip("/")
    use_model = model or (provider.get("models", ["gpt-4"])[0] if provider.get("models") else "gpt-4")

    if not api_key:
        return {
            "summary": f"No API key configured for digest generation.",
            "topics": [],
            "resources": [],
        }

    prompt = (
        "Given the following web content, provide:\n"
        "1. A concise summary (2-3 sentences)\n"
        "2. 3 relevant topics/keywords\n"
        "3. 3 links for further exploration\n\n"
        f"Content:\n{content_text[:4000]}\n\n"
        'Return as JSON: {"summary": "...", "topics": ["..."], "resources": ["..."]}'
    )

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes web content. Always respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content or ""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        return {
            "summary": result.get("summary", ""),
            "topics": result.get("topics", []),
            "resources": result.get("resources", []),
        }
    except Exception as e:
        return {
            "summary": f"Digest generation failed: {e}",
            "topics": [],
            "resources": [],
        }


def build_email_html(digest_results: list[dict], timestamp: str) -> str:
    bg = "#1a1a2e"
    card_bg = "#16213e"
    text_color = "#e0e0e0"
    secondary = "#a0a0b0"
    accent = "#0f3460"
    badge_bg = "#0f3460"
    badge_text = "#e94560"
    link_color = "#53a8b6"

    entries = ""
    for dr in digest_results:
        msg_text = dr.get("message_text", "").replace("<", "&lt;").replace(">", "&gt;")
        urls_html = ""
        for u in dr.get("urls", []):
            urls_html += f'<div style="margin:4px 0;"><a href="{u}" style="color:{link_color};text-decoration:none;font-size:13px;">{u}</a></div>'

        summary = dr.get("summary", "").replace("<", "&lt;").replace(">", "&gt;")
        topics_html = ""
        for t in dr.get("topics", []):
            t_esc = t.replace("<", "&lt;").replace(">", "&gt;")
            topics_html += f'<span style="display:inline-block;background:{badge_bg};color:{badge_text};padding:3px 10px;border-radius:12px;font-size:12px;margin:2px 4px 2px 0;">{t_esc}</span>'

        resources_html = ""
        for r in dr.get("resources", []):
            r_esc = r.replace("<", "&lt;").replace(">", "&gt;")
            resources_html += f'<div style="margin:3px 0;"><a href="{r_esc}" style="color:{link_color};text-decoration:none;font-size:13px;">{r_esc}</a></div>'

        entries += f"""
        <div style="background:{card_bg};border-radius:10px;padding:20px;margin-bottom:16px;border:1px solid #2a2a4a;">
            <div style="font-size:13px;color:{secondary};margin-bottom:8px;word-break:break-all;">{msg_text}</div>
            <div style="margin-bottom:12px;">{urls_html}</div>
            <div style="font-size:15px;color:{text_color};line-height:1.5;margin-bottom:12px;">{summary}</div>
            <div style="margin-bottom:10px;">{topics_html}</div>
            <div style="font-size:12px;color:{secondary};margin-bottom:4px;">Further Reading:</div>
            {resources_html}
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:{bg};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">
    <h1 style="font-size:22px;color:{text_color};text-align:center;margin-bottom:4px;">Fabio Telegram Digest</h1>
    <p style="font-size:13px;color:{secondary};text-align:center;margin-bottom:24px;">{timestamp}</p>
    {entries}
    <p style="font-size:11px;color:{secondary};text-align:center;margin-top:24px;">Generated by MyHub Telegram Digest</p>
</div>
</body>
</html>"""


def save_email_body(html: str, timestamp: str):
    _ensure_dirs()
    safe_ts = re.sub(r'[^\w\-]', '_', timestamp)
    filepath = os.path.join(EMAIL_BODIES_DIR, f"{safe_ts}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


def run_digest_job(config: dict) -> dict:
    result = {
        "timestamp": datetime.now().isoformat(),
        "messages_found": 0,
        "messages_processed": 0,
        "emails_sent": 0,
        "errors": [],
    }

    token = config.get("telegram_bot_token", "")
    if not token:
        result["errors"].append("No Telegram bot token configured")
        return result

    db = load_db()
    last_id = db.get("last_update_id", 0)

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": last_id + 1, "timeout": 5},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        result["errors"].append(f"Telegram API error: {e}")
        return result

    if not data.get("ok"):
        result["errors"].append(f"Telegram API returned: {data}")
        return result

    updates = data.get("result", [])
    result["messages_found"] = len(updates)

    digest_results = []
    new_last_id = last_id

    for update in updates:
        update_id = update.get("update_id", 0)
        if update_id > new_last_id:
            new_last_id = update_id

        msg = update.get("message")
        if not msg:
            continue

        msg_id = msg.get("message_id")
        if msg_id in db.get("processed_ids", []):
            continue

        text = msg.get("text", "")
        if not text:
            continue

        urls = extract_urls(text)
        if not urls:
            continue

        db.setdefault("processed_ids", []).append(msg_id)
        result["messages_processed"] += 1

        content_parts = []
        for url in urls:
            content = fetch_url_content(url)
            if content:
                content_parts.append(f"URL: {url}\n\n{content}")

        combined_content = "\n\n---\n\n".join(content_parts) if content_parts else text

        provider_index = config.get("digest_llm_provider", 0)
        model = config.get("digest_llm_model", "")

        try:
            digest = generate_digest(combined_content, text, provider_index, model)
        except Exception as e:
            result["errors"].append(f"Digest gen failed for msg {msg_id}: {e}")
            digest = {
                "summary": f"Error generating digest: {e}",
                "topics": [],
                "resources": [],
            }

        digest_results.append({
            "message_text": text,
            "urls": urls,
            "summary": digest.get("summary", ""),
            "topics": digest.get("topics", []),
            "resources": digest.get("resources", []),
        })

    if digest_results:
        ts = result["timestamp"]
        html = build_email_html(digest_results, ts)
        save_email_body(html, ts)

        subject = f"Fabio Telegram Digest - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        from backend.services.email_sender import send_email
        email_result = send_email(subject, html, config)
        if email_result.get("ok"):
            result["emails_sent"] = 1
        else:
            result["errors"].append(f"Email send failed: {email_result.get('error', 'unknown')}")

    db["last_update_id"] = new_last_id
    db["total_processed"] = db.get("total_processed", 0) + result["messages_processed"]
    db["total_emails"] = db.get("total_emails", 0) + result["emails_sent"]

    processed_ids = db.get("processed_ids", [])
    if len(processed_ids) > 1000:
        db["processed_ids"] = processed_ids[-500:]

    db.setdefault("history", []).append({
        "timestamp": result["timestamp"],
        "messages_found": result["messages_found"],
        "messages_processed": result["messages_processed"],
        "emails_sent": result["emails_sent"],
        "errors": result["errors"],
    })
    if len(db["history"]) > 100:
        db["history"] = db["history"][-100:]

    save_db(db)
    return result
