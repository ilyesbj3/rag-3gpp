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


# Cross-spec questions written for the router only (independent of eval/testset.json): they
# mix architecture (Stage 2) and NAS (Stage 3) vocabulary and must search both specs.
CROSS_LABELED = [
    "Explain how the AMF handles registration and which NAS messages it exchanges with the UE.",
    "What is a QoS flow and how are QoS rules signalled to the UE in NAS?",
    "How does network slice selection work and how is the requested NSSAI carried in the "
    "REGISTRATION REQUEST?",
    "Describe the PDU session establishment procedure and the 5GSM messages involved.",
    "How does the SMF select a UPF, and what does the PDU SESSION ESTABLISHMENT ACCEPT contain?",
    "What is the role of the AUSF in authentication and which NAS messages carry the challenge?",
    "How do SSC modes work and how is the SSC mode indicated in the PDU session request?",
    "Explain mobility registration update in the architecture and the NAS timers involved.",
    "What does the registration area mean and how is the TAI list encoded in the "
    "REGISTRATION ACCEPT message?",
    "How is the user plane reactivated with the service request procedure, and which messages "
    "are exchanged?",
    "How are home-routed roaming PDU sessions handled and which 5GSM cause values can be returned?",
    "Describe UE configuration update: the role of the AMF and the CONFIGURATION UPDATE "
    "COMMAND message.",
]


@pytest.mark.parametrize("question", CROSS_LABELED)
def test_cross_spec_questions_search_both(question):
    assert route(question).specs == BOTH


# Single-spec guards: the cross-spec rules must not over-route these.
SINGLE_GUARDS = [
    ("What is the coding of the 5GS mobile identity information element?", {TS24}),
    ("When does the UE stop timer T3511?", {TS24}),
    ("What is the purpose of the 5GMM cause #7?", {TS24}),
    ("Which reference points does the NEF use?", {TS23}),
    ("What is the role of the PCF in the architecture?", {TS23}),
    ("Describe local breakout roaming architecture.", {TS23}),
]


@pytest.mark.parametrize("question,expected", SINGLE_GUARDS)
def test_single_spec_guards(question, expected):
    assert route(question).specs == expected


def test_router_version_1_keeps_original_rules():
    q = "Describe the PDU session establishment procedure and the 5GSM messages involved."
    assert route(q, version=1).specs == {TS24}  # original rules: NAS words dominate
    assert route(q, version=2).specs == BOTH
