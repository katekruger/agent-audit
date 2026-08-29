#!/usr/bin/env python3
"""Validate an example file (a record, or a list of records) against a
JSON Schema. Used by CI's validate-examples job; safe to run locally.

Usage: validate_example.py <schema.json> <example.json>
"""

import json
import sys

from jsonschema import validate


def main() -> int:
    schema_path, example_path = sys.argv[1], sys.argv[2]
    schema = json.loads(open(schema_path).read())
    data = json.loads(open(example_path).read())
    records = data if isinstance(data, list) else [data]
    for record in records:
        validate(instance=record, schema=schema)
    print(f"OK: {example_path} ({len(records)} record(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
