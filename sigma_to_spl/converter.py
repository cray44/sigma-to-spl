from pathlib import Path

from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
from sigma.rule import SigmaRule

from .config import SplunkConfig
from .postprocess import PostProcessor


class ConversionError(Exception):
    pass


class Converter:
    def __init__(self, config: SplunkConfig):
        self.config = config
        self.backend = SplunkBackend()
        self.postprocessor = PostProcessor(config)

    def convert_file(self, rule_path: Path) -> str:
        try:
            collection = SigmaCollection.load_ruleset([rule_path])
        except Exception as e:
            raise ConversionError(f"Failed to parse {rule_path.name}: {e}") from e

        try:
            queries = self.backend.convert(collection)
        except Exception as e:
            raise ConversionError(f"Failed to convert {rule_path.name}: {e}") from e

        if not queries:
            raise ConversionError(f"No output produced for {rule_path.name}")

        rule = list(collection)[0]
        spl = queries[0]
        return self.postprocessor.apply(spl, rule, rule_path)

    def convert_directory(self, rules_dir: Path) -> dict[str, str]:
        results = {}
        for rule_path in sorted(rules_dir.rglob("*.yml")):
            try:
                results[rule_path.name] = self.convert_file(rule_path)
            except ConversionError as e:
                results[rule_path.name] = f"# ERROR: {e}"
        return results
