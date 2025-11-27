from dataclasses import dataclass
from typing import List,Dict
from pydantic import BaseModel, Field

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

class SecurityViewDimensions(BaseModel):
    """
    Pydantic model for storing the three core dimensions of a security view.
    """

    V_Asset_Security: str = Field(
        description="Asset Security Dimension (V_Asset_Security): Assesses the code's protection of critical assets like underlying resources, memory, or configuration. E.g., issues like memory leaks, buffer overflows, or sensitive hardcoded configuration."
    )

    V_Access_Control: str = Field(
        description="Access Control Dimension (V_Access_Control): Evaluates the effectiveness of the code in authentication, authorization, and permission management. E.g., flaws like privilege escalation, unauthorized access, or broken access control."
    )

    V_Data_Logic: str = Field(
        description="Data and Logic Dimension (V_Data_Logic): Assesses the code's handling of input data, the correctness of business logic, and the security of the data flow. E.g., problems like insufficient input validation, business logic flaws, or data leakage."
    )
class DimensionFinding(BaseModel):
    """Model for individual security dimension findings"""
    finding: str = Field(description="Detailed description of the vulnerability")
    risk_level: str = Field(description="Risk level (Critical/High/Medium/Low)")
    vulnerability_type: str = Field(description="Type of vulnerability")
    code_location: str = Field(description="Location of problematic code")
    remediation: str = Field(description="Remediation recommendations")

class SecurityViewDimensionsExtended(BaseModel):
    """Extended security view dimensions with detailed findings"""
    V_Asset_Security: DimensionFinding = Field(description="Asset Security Dimension findings")
    V_Access_Control: DimensionFinding = Field(description="Access Control Dimension findings")
    V_Data_Logic: DimensionFinding = Field(description="Data and Logic Dimension findings")

class VulnerabilitySummary(BaseModel):
    """Summary of vulnerabilities by severity"""
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int

class AuditReport(BaseModel):
    """Complete security audit report model"""
    report_metadata: dict = Field(description="Report metadata and context")
    security_view_dimensions: SecurityViewDimensionsExtended = Field(description="Three core security dimensions")
    vulnerability_summary: VulnerabilitySummary = Field(description="Vulnerability severity summary")
    recommendation_summary: dict = Field(description="Summary of recommendations")
    conclusion: str = Field(description="Overall audit conclusion")