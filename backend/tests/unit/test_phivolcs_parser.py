from ingestion.scraping.parsers import text_from_html


def test_text_from_html_removes_tags():
    assert text_from_html("<main><h1>Bulletin</h1><p>Alert Level 1</p></main>") == (
        "Bulletin Alert Level 1"
    )
