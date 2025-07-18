from ..analyzer import Wikipedia, Analyzer

def test_wiki_page_loading():
    wiki = Wikipedia("Seabrooke")

    assert wiki.text is not None
    assert wiki.links is not None
    assert len(wiki.links) == 6
