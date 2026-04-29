from pathlib import Path
import pytest

from sigma_to_spl.config import default_config
from sigma_to_spl.converter import Converter


RULES_DIR = Path(__file__).parent.parent / "rules"


def test_convert_dns_tunneling_rule():
    rule_path = RULES_DIR / "network" / "dns-tunneling-high-entropy-subdomains.yml"
    assert rule_path.exists(), f"Rule file not found: {rule_path}"

    converter = Converter(default_config())
    result = converter.convert_file(rule_path)

    assert result
    assert "ERROR" not in result
    assert "qtype_name" in result or "query" in result


def test_convert_directory_no_crash():
    converter = Converter(default_config())
    results = converter.convert_directory(RULES_DIR)

    assert len(results) > 0
    errors = [name for name, spl in results.items() if spl.startswith("# ERROR")]
    assert not errors, f"Conversion errors: {errors}"
