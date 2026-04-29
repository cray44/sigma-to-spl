import yaml
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class SplunkConfig:
    index_map: dict = field(default_factory=dict)
    field_map: dict = field(default_factory=dict)
    macros: dict = field(default_factory=dict)
    default_index: str = "index=main"


def load_config(config_path: Path) -> SplunkConfig:
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return SplunkConfig(
        index_map=raw.get("index_map", {}),
        field_map=raw.get("field_map", {}),
        macros=raw.get("macros", {}),
        default_index=raw.get("default_index", "index=main"),
    )


def default_config() -> SplunkConfig:
    defaults_path = Path(__file__).parent.parent / "config" / "corelight.yml"
    if defaults_path.exists():
        return load_config(defaults_path)
    return SplunkConfig()
