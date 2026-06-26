def generate_card_html(url: str, title: str = "", description: str = "", image_url: str = "", theme: str = "dark") -> str:
    bg = "#1e293b" if theme == "dark" else "#f1f5f9"
    text_color = "#e2e8f0" if theme == "dark" else "#1e293b"
    secondary_color = "#94a3b8" if theme == "dark" else "#64748b"
    border_color = "#334155" if theme == "dark" else "#cbd5e1"

    display_title = title or url
    display_desc = description or ""
    img_tag = f'<img src="{image_url}" alt="preview" style="width:100%;height:180px;object-fit:cover;border-radius:8px 8px 0 0;" />' if image_url else ""

    return f"""<div style="max-width:480px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;border:1px solid {border_color};border-radius:12px;overflow:hidden;background:{bg};box-shadow:0 4px 12px rgba(0,0,0,0.15);">
  {img_tag}
  <div style="padding:16px;">
    <div style="font-size:16px;font-weight:600;color:{text_color};margin-bottom:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_escape(display_title)}</div>
    <div style="font-size:14px;color:{secondary_color};margin-bottom:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{_escape(display_desc)}</div>
    <a href="{_escape(url)}" target="_blank" style="font-size:13px;color:#3b82f6;text-decoration:none;">{_escape(_extract_domain(url))} &rarr;</a>
  </div>
</div>"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url


class _OGParser:
    def __init__(self):
        from html.parser import HTMLParser
        self._html_parser = HTMLParser
        self.og_title = ""
        self.og_description = ""
        self.og_image = ""
        self.title = ""
        self._in_title = False

    def parse(self, html: str):
        class Parser(self._html_parser):
            def __init__(self_p, outer):
                super().__init__()
                self_p.outer = outer

            def handle_starttag(self_p, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "title":
                    self_p.outer._in_title = True
                if tag == "meta":
                    prop = attrs_dict.get("property", "") or attrs_dict.get("name", "")
                    content = attrs_dict.get("content", "")
                    if prop == "og:title":
                        self_p.outer.og_title = content
                    elif prop == "og:description":
                        self_p.outer.og_description = content
                    elif prop == "og:image":
                        self_p.outer.og_image = content
                    elif prop == "description" and not self_p.outer.og_description:
                        self_p.outer.og_description = content

            def handle_data(self_p, data):
                if self_p.outer._in_title:
                    self_p.outer.title += data

            def handle_endtag(self_p, tag):
                if tag == "title":
                    self_p.outer._in_title = False

        p = Parser(self)
        p.feed(html)


def fetch_metadata(url: str) -> dict:
    import requests as _requests
    from urllib.parse import urlparse
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = _requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()

        parser = _OGParser()
        parser.parse(resp.text[:50000])

        title = parser.og_title or parser.title or ""
        description = parser.og_description or ""
        image_url = parser.og_image or ""

        if image_url and not image_url.startswith(("http://", "https://")):
            parsed = urlparse(url)
            image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

        return {"title": title.strip(), "description": description.strip(), "image_url": image_url.strip()}
    except Exception as e:
        return {"title": "", "description": "", "image_url": "", "error": str(e)}
