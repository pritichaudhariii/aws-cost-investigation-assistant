from costassist.knowledge import _front_matter
from costassist.pii import contains_pii, redact


def test_front_matter_parsing():
    meta, body = _front_matter("---\ntitle: T\nallowed_roles: finance, admin\n---\n# T\nbody")
    assert meta["title"] == "T"
    assert meta["allowed_roles"] == ["finance", "admin"]
    assert body.startswith("# T")


def test_every_chunk_has_roles_and_category(chunks):
    assert len({c.doc_id for c in chunks}) == 13
    for c in chunks:
        assert c.allowed_roles, c.doc_id
        assert c.metadata.get("category"), c.doc_id
        assert len(c.text) <= 900


def test_restricted_docs_are_not_visible_to_engineers(chunks):
    restricted = {c.doc_id for c in chunks if "engineer" not in c.allowed_roles}
    assert restricted == {"commitments_finance", "escalation_contacts_admin"}


def test_redaction():
    text = ("mail ops@example.com or call +1 206-555-0142 from 10.1.2.3, key AKIAIOSFODNN7EXAMPLE "
            "secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    out, counts = redact(text)
    assert counts == {"EMAIL": 1, "AWS_ACCESS_KEY": 1, "AWS_SECRET": 1, "PHONE": 1, "IP": 1}
    assert not contains_pii(out)


def test_redaction_leaves_cost_text_alone():
    text = "USE1-NatGateway-Bytes on nat-payments-a rose from $7.00 to $260.00 per day; account 210987654321"
    assert redact(text) == (text, {})
