from services.pii_redaction.redactor import redact_text


def test_redact_text_replaces_common_sensitive_values():
    result = redact_text(
        "Email me at customer@example.com or +1 (555) 123-4567. "
        "Order ORD-12345 used card 4242 4242 4242 4242."
    )

    assert "customer@example.com" not in result.text
    assert "4242 4242 4242 4242" not in result.text
    assert "[REDACTED_EMAIL]" in result.text
    assert result.counts["email"] == 1
    assert result.counts["card"] == 1
