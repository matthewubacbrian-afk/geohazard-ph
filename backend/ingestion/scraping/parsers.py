from bs4 import BeautifulSoup


def text_from_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
