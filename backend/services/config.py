import json
import os

CONFIG_FILE = "app_config.json"

DEFAULTS = {
    "app_name": "MyHub",
    "providers": [
        {
            "name": "Provider 1",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "models": ["gpt-4", "gpt-4o", "gpt-3.5-turbo"],
        },
        {
            "name": "Provider 2",
            "base_url": "",
            "api_key": "",
            "models": [],
        },
    ],
    "active_provider": 0,
    "wiki_dir": "./wiki/",
    "card_theme": "dark",
    "telegram_bot_token": "",
    "gmail_address": "",
    "gmail_app_password": "",
    "recipient_email": "",
    "digest_llm_provider": 0,
    "digest_llm_model": "",
    "telegram_files_dir": "./telegram_files/",
    "digest_cron": "0 8 * * *",
    "weekly_digest_cron": "0 9 * * 1",
    "files_cron": "*/30 * * * *",
}


def _config_path() -> str:
    if getattr(__import__("sys"), "frozen", False):
        base = os.path.dirname(__import__("sys").executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, CONFIG_FILE)


def load_config() -> dict:
    path = _config_path()
    config = dict(DEFAULTS)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        config.update(saved)
    if "providers" not in config:
        config["providers"] = DEFAULTS["providers"]
    if "active_provider" not in config:
        config["active_provider"] = 0
    return config


def save_config(config: dict):
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_active_provider(config: dict) -> dict:
    idx = config.get("active_provider", 0)
    providers = config.get("providers", [])
    if 0 <= idx < len(providers):
        return providers[idx]
    return {}


def get_all_models(config: dict) -> list[str]:
    models = []
    for p in config.get("providers", []):
        models.extend(p.get("models", []))
    return models
