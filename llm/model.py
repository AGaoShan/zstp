from dataclasses import dataclass
from typing import List


@dataclass
class RootCauseAnalysis:
    """漏洞根本原因分析类"""
    logic_flow: List[str]
    violated_invariant: str

@dataclass
class RemediationSuggestion:
    """修复建议类"""
    technique: str
    code_change: str

@dataclass
class VulnerabilityReport:
    """漏洞报告主类"""
    vulnerability_type: str
    severity: str
    root_cause_analysis: RootCauseAnalysis
    code_pattern_abstract: str
    impact: str
    remediation_suggestion: RemediationSuggestion
    false_positive_indicators: str