from core.domains.auto import DEFAULT_AUTO_DOMAIN_ID, infer_domain_id


def test_infer_domain_uses_transcript_keywords():
    transcript = (
        "The prospect asked about budget, the buying process, security review, "
        "and whether a pilot could start before the proposal is signed."
    )

    assert infer_domain_id(transcript) == "sales"


def test_infer_domain_uses_filename_hints():
    assert infer_domain_id("The conversation was short.", "customer_support_refund.wav") == (
        "customer_support"
    )


def test_infer_domain_falls_back_to_default():
    assert infer_domain_id("A generic conversation without clear business terms.") == (
        DEFAULT_AUTO_DOMAIN_ID
    )
