import re


class SecurityService:
    sensitive_patterns = [(r"\b(?:\d[ -]?){13,19}\b", "payment-card-like number"), (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "email address"), (r"\b[A-Z]{1,2}\d{6,9}\b", "identifier-like token")]
    injection_patterns = [r"ignore (all |previous |prior )?instructions", r"reveal (the )?(system|hidden) prompt", r"bypass (security|access|guardrails)", r"jailbreak"]

    def controls_for_query(self, query: str) -> list[str]:
        controls = [f"audit-redaction:{label}" for pattern, label in self.sensitive_patterns if re.search(pattern, query, re.I)]
        if any(re.search(pattern, query, re.I) for pattern in self.injection_patterns): controls.append("prompt-injection-block")
        return controls
