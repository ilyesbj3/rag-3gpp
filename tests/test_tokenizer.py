from src.ingest.tokenizer import tokenize


def test_cause_with_hash():
    toks = tokenize("What does cause #9 mean?")
    assert "cause_9" in toks and "cause" in toks


def test_cause_without_hash_and_with_value():
    assert "cause_9" in tokenize("5GMM cause 9")
    assert "cause_27" in tokenize("cause value 27")
    assert "cause_9" in tokenize("Cause #9 – UE identity cannot be derived by the network.")


def test_plain_number_is_not_a_cause():
    assert not any(t.startswith("cause_") for t in tokenize("there are 9 octets"))


def test_timer_kept_whole():
    assert tokenize("T3510 expiry") == ["t3510", "expiry"]


def test_hyphenated_acronym_and_variant():
    toks = tokenize("S-NSSAI")
    assert toks[:2] == ["s-nssai", "snssai"]
    assert "nssai" in toks and "s" not in toks


def test_alnum_acronyms():
    assert tokenize("5GMM") == ["5gmm"]
    assert tokenize("N2 interface") == ["n2", "interface"]
    assert tokenize("5G-GUTI")[:2] == ["5g-guti", "5gguti"]


def test_message_names_are_not_stopwords():
    assert tokenize("REGISTRATION REQUEST") == ["registration", "request"]
    assert "reject" in tokenize("the network sends a REGISTRATION REJECT")


def test_section_reference():
    assert tokenize("section 5.5.1.2.4") == ["section", "5.5.1.2.4"]
    assert "5.35a.1" in tokenize("see clause 5.35A.1")


def test_stopwords_removed_and_stemming_optional():
    assert tokenize("the role of the AMF") == ["role", "amf"]
    assert tokenize("registrations", stem=True) == tokenize("registration", stem=True)
    assert tokenize("registrations") == ["registrations"]
