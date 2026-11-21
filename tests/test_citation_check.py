from src.generation.citation_check import NOT_GROUNDED, check_citations
from src.generation.llm import REFUSAL

LABELS = {("TS 24.501", "5.5.1.2.4"), ("TS 24.501", "A.1"), ("TS 23.501", "5.35A.1")}


def test_valid_citation_kept():
    r = check_citations("The AMF accepts it [TS 24.501 §5.5.1.2.4].", LABELS)
    assert r.text == "The AMF accepts it [TS 24.501 §5.5.1.2.4]."
    assert [(c.section, c.valid, c.loose) for c in r.citations] == [("5.5.1.2.4", True, False)]
    assert r.warnings == [] and not r.refused


def test_invalid_citation_removed_with_warning():
    r = check_citations("Fact [TS 24.501 §5.5.1.2.4]. Other [TS 24.501 §9.9.9].", LABELS)
    assert r.text == "Fact [TS 24.501 §5.5.1.2.4]. Other."
    assert [c.valid for c in r.citations] == [True, False]
    assert any("9.9.9" in w for w in r.warnings)


def test_ancestor_is_loose_valid():
    r = check_citations("Registration [TS 24.501 §5.5.1].", LABELS)
    c = r.citations[0]
    assert c.valid and c.loose
    assert "[TS 24.501 §5.5.1]" in r.text


def test_variants_and_multiple_in_one_bracket():
    r = check_citations("X [TS24.501 Section A.1; TS 23.501 § 5.35A.1].", LABELS)
    assert r.text == "X [TS 24.501 §A.1][TS 23.501 §5.35A.1]."
    assert all(c.valid for c in r.citations)


def test_lettered_section_not_confused_with_prefix():
    r = check_citations("Y [TS 23.501 §5.35].", LABELS)
    assert r.citations[0].valid is False  # 5.35 is not an ancestor of 5.35A.1


def test_no_citation_warns_not_grounded():
    r = check_citations("The AMF does things.", LABELS)
    assert NOT_GROUNDED in r.warnings


def test_refusal_normalized():
    r = check_citations("Sorry. " + REFUSAL + " [TS 24.501 §A.1]", LABELS)
    assert r.refused and r.text == REFUSAL and r.citations == []
