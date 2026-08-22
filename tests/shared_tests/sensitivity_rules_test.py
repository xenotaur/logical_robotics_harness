import unittest

from lrh.shared import sensitivity_rules


class TestSensitivityRules(unittest.TestCase):
    def test_basic_rules_cover_expected_categories(self) -> None:
        categories = {rule.category for rule in sensitivity_rules._BASIC_RULES}

        self.assertEqual(
            categories,
            {
                "email",
                "government_id",
                "private_key",
                "token",
                "url_credentials",
                "phone",
            },
        )

    def test_basic_rules_use_declared_severity_and_confidence_values(self) -> None:
        allowed_severities = {
            sensitivity_rules.SEVERITY_MEDIUM,
            sensitivity_rules.SEVERITY_HIGH,
        }
        allowed_confidences = {
            sensitivity_rules.CONFIDENCE_MEDIUM,
            sensitivity_rules.CONFIDENCE_HIGH,
        }

        for rule in sensitivity_rules._BASIC_RULES:
            self.assertIn(rule.severity, allowed_severities)
            self.assertIn(rule.confidence, allowed_confidences)

    def test_email_pattern_matches_basic_address(self) -> None:
        match = sensitivity_rules._EMAIL_PATTERN.search("Contact user@example.com now")

        self.assertIsNotNone(match)
        self.assertEqual(match.group(0), "user@example.com")

    def test_secret_assignment_pattern_captures_key_and_value(self) -> None:
        match = sensitivity_rules._SECRET_ASSIGNMENT_PATTERN.search(
            "password = swordfish"
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.group("key"), "password")

    def test_digits_only_strips_non_digit_characters(self) -> None:
        self.assertEqual(
            sensitivity_rules._digits_only("4111 1111-1111 1111"), "4111111111111111"
        )

    def test_passes_luhn_check_accepts_valid_number(self) -> None:
        self.assertTrue(sensitivity_rules._passes_luhn_check("4111111111111111"))

    def test_passes_luhn_check_rejects_invalid_number(self) -> None:
        self.assertFalse(sensitivity_rules._passes_luhn_check("4111111111111112"))

    def test_is_valid_ipv4_address_accepts_well_formed_address(self) -> None:
        self.assertTrue(sensitivity_rules._is_valid_ipv4_address("192.168.0.1"))

    def test_is_valid_ipv4_address_rejects_out_of_range_octet(self) -> None:
        self.assertFalse(sensitivity_rules._is_valid_ipv4_address("999.168.0.1"))

    def test_is_valid_ipv4_address_rejects_wrong_octet_count(self) -> None:
        self.assertFalse(sensitivity_rules._is_valid_ipv4_address("192.168.1"))


if __name__ == "__main__":
    unittest.main()
