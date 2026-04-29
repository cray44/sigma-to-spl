from pathlib import Path

from sigma.rule import SigmaRule

from .config import SplunkConfig

# Sigma logsource categories that need a manual entropy note
ENTROPY_REQUIRED_CATEGORIES = {"dns"}

# Sigma logsource categories we know need a manual review note
COMPLEX_AGGREGATION_KEYWORDS = ("count by", "max(", "min(", "avg(", "dc(")


class PostProcessor:
    def __init__(self, config: SplunkConfig):
        self.config = config

    def apply(self, spl: str, rule: SigmaRule, rule_path: Path) -> str:
        headers = self._build_headers(spl, rule)
        spl = self._inject_index(spl, rule)
        spl = self._apply_field_map(spl)
        spl = self._apply_macros(spl)
        return headers + spl

    def _build_headers(self, spl: str, rule: SigmaRule) -> str:
        lines = []
        lines.append(f"| title: {rule.title}")
        if rule.id:
            lines.append(f"| id: {rule.id}")
        lines.append(f"| status: {rule.status.name.lower()}")
        if rule.description:
            lines.append(f"| description: {rule.description}")

        category = getattr(rule.logsource, "category", None) or ""
        if category in ENTROPY_REQUIRED_CATEGORIES:
            lines.append("| MANUAL: this rule category may require entropy scoring — see detection writeup for SPL additions")

        if any(kw in spl for kw in COMPLEX_AGGREGATION_KEYWORDS):
            lines.append("| MANUAL: complex aggregation detected — verify stats logic matches intent")

        return "\n".join(f"* {l}" for l in lines) + "\n\n"

    def _inject_index(self, spl: str, rule: SigmaRule) -> str:
        category = getattr(rule.logsource, "category", None) or ""
        product = getattr(rule.logsource, "product", None) or ""

        key = category or product
        index_prefix = self.config.index_map.get(key, self.config.default_index)

        if not spl.strip().startswith("index=") and not spl.strip().startswith("`"):
            return f"{index_prefix}\n| {spl}" if "|" in spl else f"{index_prefix} {spl}"
        return spl

    def _apply_field_map(self, spl: str) -> str:
        for generic, specific in self.config.field_map.items():
            spl = spl.replace(generic, specific)
        return spl

    def _apply_macros(self, spl: str) -> str:
        for pattern, macro in self.config.macros.items():
            spl = spl.replace(pattern, macro)
        return spl


def format_savedsearches(title: str, spl: str) -> str:
    safe_title = title.replace(" ", "_").lower()
    return (
        f"[{safe_title}]\n"
        f"search = {spl}\n"
        f"dispatch.earliest_time = -24h\n"
        f"dispatch.latest_time = now\n"
        f"enableSched = 1\n"
        f"cron_schedule = 0 * * * *\n"
        f"alert.track = 1\n"
    )
