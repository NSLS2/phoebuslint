from .rules import LintRule, RecursiveLintRule
from .utils import SeverityLevel
import yaml

class PhoebusLintConfig:
    def __init__(self, fail_severity: SeverityLevel = SeverityLevel.WARNING, disabled_rules: list[type[LintRule] | type[RecursiveLintRule]] = []):
        self._enabled_rules = LintRule.__subclasses__() + RecursiveLintRule.__subclasses__()
        for disabled_rule in disabled_rules:
            self._enabled_rules.remove(disabled_rule)
        self._fail_severity = fail_severity

    @property
    def rules(self) -> list[type[LintRule] | type[RecursiveLintRule]]:
        return self._enabled_rules

    def is_rule_enabled(self, rule: type[LintRule] | type[RecursiveLintRule]) -> bool:
        return rule in self._enabled_rules

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'PhoebusLintConfig':
        data = yaml.safe_load(yaml_content)
        disabled_rule_codes = data.get('disabled_rules', [])
        fail_severity = SeverityLevel[data.get('fail_severity', 'warning').upper()]
        return cls(fail_severity=fail_severity, disabled_rules=disabled_rule_codes)