"""Router on a labeled question set, separate from the evaluation test set."""

import pytest

from src.retrieval.router import BOTH, TS23, TS24, route

LABELED = [
    ("What does 5GMM cause #22 indicate?", {TS24}),
    ("When is timer T3346 started?", {TS24}),
    ("Which information elements are optional in the SERVICE REQUEST message?", {TS24}),
    ("How is the 5GSM cause information element coded?", {TS24}),
    ("What happens when the UE receives a REGISTRATION REJECT?", {TS24}),
    ("What is the message type value of the IDENTITY RESPONSE?", {TS24}),
    ("What is the role of the NSSF?", {TS23}),
    ("Which reference point connects the SMF and the UPF?", {TS23}),
    ("What are the SSC modes?", {TS23}),
    ("What are the QoS characteristics of 5QI 1?", {TS23}),
    ("Explain home-routed roaming architecture.", {TS23}),
    ("What is network slicing in 5G?", {TS23}),
    (
        "Describe the registration procedure and the NAS messages exchanged "
        "between the UE and the AMF.",
        BOTH,
    ),
    ("Explain end-to-end PDU session establishment.", BOTH),
    ("What is the weather like?", BOTH),
    ("According to TS 24.501, what is the AMF?", {TS24}),
    ("What does TS 23.501 say about the registration area?", {TS23}),
]


@pytest.mark.parametrize("question,expected", LABELED)
def test_labeled_routes(question, expected):
    assert route(question).specs == expected


def test_routing_disabled_searches_both():
    d = route("What does 5GMM cause #9 mean?", use_routing=False)
    assert d.specs == BOTH and d.reason == "routing disabled"


def test_nf_name_without_role_context_is_not_23501_signal():
    d = route("Which timer does the AMF start?")
    assert d.scores[TS23] == 0
