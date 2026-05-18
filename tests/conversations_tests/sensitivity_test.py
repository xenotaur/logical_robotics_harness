import unittest

from lrh.conversations import sensitivity


class TestSensitivityScanner(unittest.TestCase):
    def _rule_ids_for(self, text: str) -> set[str]:
        result = sensitivity.scan_text_for_sensitive_findings(text)
        return {finding.rule_id for finding in result.findings}

    def test_detects_email(self) -> None:
        result = sensitivity.scan_text_for_sensitive_findings(
            "Contact support@example.com for details."
        )

        self.assertEqual(result.status, sensitivity.STATUS_POTENTIAL)
        self.assertIn("email.basic", self._rule_ids_for("Email: user@example.com"))
        self.assertEqual(result.findings[0].redacted_preview, "<EMAIL>")

    def test_detects_us_ssn_like_pattern(self) -> None:
        rule_ids = self._rule_ids_for("Candidate SSN is 123-45-6789.")

        self.assertIn("ssn.us", rule_ids)

    def test_detects_private_key_block(self) -> None:
        text = """Key:
-----BEGIN PRIVATE KEY-----
abc123
-----END PRIVATE KEY-----
"""

        result = sensitivity.scan_text_for_sensitive_findings(text)

        self.assertEqual(result.findings[0].rule_id, "private_key.pem_block")
        self.assertEqual(result.findings[0].redacted_preview, "<PRIVATE_KEY_BLOCK>")

    def test_detects_password_or_secret_assignment(self) -> None:
        result = sensitivity.scan_text_for_sensitive_findings("password = swordfish")

        self.assertEqual(result.findings[0].rule_id, "secret.keyword_assignment")
        self.assertEqual(result.findings[0].redacted_preview, "password=<REDACTED>")

    def test_detects_known_token_prefix(self) -> None:
        token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
        rule_ids = self._rule_ids_for(f"token: {token}")

        self.assertIn("token.known_prefix", rule_ids)

    def test_detects_url_with_credentials(self) -> None:
        text = "Fetch https://user:pass@example.com/private.git"
        result = sensitivity.scan_text_for_sensitive_findings(text)

        self.assertIn("url.credentials", self._rule_ids_for(text))
        self.assertIn("<URL_WITH_CREDENTIALS>", result.findings[0].redacted_preview)

    def test_detects_luhn_valid_credit_card_like_number(self) -> None:
        text = "Card 4111 1111 1111 1111 was pasted."
        rule_ids = self._rule_ids_for(text)

        self.assertIn("credit_card.luhn", rule_ids)

    def test_does_not_detect_invalid_luhn_number_as_credit_card(self) -> None:
        text = "Order number 4111 1111 1111 1112 is not a card."
        result = sensitivity.scan_text_for_sensitive_findings(text)

        self.assertNotIn(
            "credit_card.luhn", {finding.rule_id for finding in result.findings}
        )

    def test_redacted_preview_does_not_store_raw_secret_or_token(self) -> None:
        text = "api_key = super-secret-value sk-abcdefghijklmnop123456"
        result = sensitivity.scan_text_for_sensitive_findings(text)

        previews = [finding.redacted_preview for finding in result.findings]
        self.assertNotIn("super-secret-value", previews)
        self.assertNotIn("sk-abcdefghijklmnop123456", previews)
        self.assertIn("api_key=<REDACTED>", previews)
        self.assertIn("<TOKEN>", previews)

    def test_returns_none_detected_for_ordinary_text(self) -> None:
        result = sensitivity.scan_text_for_sensitive_findings(
            "We discussed roadmap scope, validation tests, and review notes."
        )

        self.assertEqual(result.status, sensitivity.STATUS_NONE_DETECTED)
        self.assertEqual(result.finding_count, 0)
        self.assertEqual(result.categories, ())
        self.assertEqual(result.findings, ())

    def test_returns_stable_categories_in_deterministic_order(self) -> None:
        text = """Reach admin@example.com.
The server is 192.168.0.1.
Use 4111 1111 1111 1111 only in tests.
"""

        result = sensitivity.scan_text_for_sensitive_findings(text)

        self.assertEqual(result.categories, ("credit_card", "email", "ip_address"))

    def test_detects_basic_ip_address_and_us_like_phone(self) -> None:
        text = "Host 10.0.0.1 and phone (212) 555-0199 were pasted."
        rule_ids = self._rule_ids_for(text)

        self.assertIn("ip_address.basic", rule_ids)
        self.assertIn("phone.us_like", rule_ids)


if __name__ == "__main__":
    unittest.main()
