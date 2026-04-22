import json
import unittest
from pathlib import Path


class TestWorkItemSchemaContract(unittest.TestCase):
    def test_schema_requires_type_and_restricts_allowed_values(self) -> None:
        schema_path = Path("project/design/schemas/work_item_metadata.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertIn("type", schema["required"])
        self.assertEqual(
            schema["properties"]["type"]["enum"],
            ["deliverable", "investigation", "evaluation", "operation"],
        )


if __name__ == "__main__":
    unittest.main()
