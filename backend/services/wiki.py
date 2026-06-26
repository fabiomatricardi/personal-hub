import os
from backend.services.config import load_config


def get_wiki_dir() -> str:
    config = load_config()
    return config.get("wiki_dir", "./wiki/")


def list_files() -> list[dict]:
    wiki_dir = get_wiki_dir()
    if not os.path.isdir(wiki_dir):
        return []
    files = []
    for fname in sorted(os.listdir(wiki_dir)):
        if not fname.endswith((".md", ".txt")):
            continue
        filepath = os.path.join(wiki_dir, fname)
        if not os.path.isfile(filepath):
            continue
        title = _extract_title(filepath, fname)
        files.append({"name": fname, "title": title})
    return files


def read_file(name: str) -> dict | None:
    wiki_dir = get_wiki_dir()
    filepath = os.path.join(wiki_dir, name)
    if not os.path.isfile(filepath):
        return None
    title = _extract_title(filepath, name)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"name": name, "title": title, "content": content}


def _extract_title(filepath: str, fallback: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line.startswith("#"):
            return first_line.lstrip("#").strip()
        return first_line if first_line else fallback
    except Exception:
        return fallback
