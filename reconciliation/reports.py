"""
Report Generation Module
Based on DMaaS Playbook Section 4E

Provides:
- Evidence Pack Generation (PDF/JSON)
- Reconciliation Report Generation
- Acceptance Test Results
- Domain-by-domain status reports
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import hashlib


@dataclass
class DomainStatus:
    """Status of a specific data domain."""
    domain: str
    status: str  # passed, warning, failed
    checks_passed: int
    checks_total: int
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "status": self.status,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "pass_rate": self.checks_passed / self.checks_total if self.checks_total > 0 else 0,
            "issues": self.issues,
            "metrics": self.metrics,
        }


@dataclass
class EvidencePack:
    """
    Evidence pack for migration verification.
    Contains all artifacts needed to verify migration success.
    """
    id: str
    created_at: datetime
    migration_id: str
    source_systems: List[str]
    target_system: str
    domain_statuses: List[DomainStatus] = field(default_factory=list)
    reconciliation_results: List[Dict[str, Any]] = field(default_factory=list)
    sample_verifications: List[Dict[str, Any]] = field(default_factory=list)
    data_hashes: Dict[str, str] = field(default_factory=dict)
    overall_status: str = "pending"
    approval_status: str = "pending"
    approver: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    notes: str = ""

    def calculate_overall_status(self) -> str:
        """Calculate overall status from domain statuses."""
        if not self.domain_statuses:
            return "pending"

        failed = sum(1 for d in self.domain_statuses if d.status == "failed")
        warnings = sum(1 for d in self.domain_statuses if d.status == "warning")

        if failed > 0:
            self.overall_status = "failed"
        elif warnings > 0:
            self.overall_status = "warning"
        else:
            self.overall_status = "passed"

        return self.overall_status

    def generate_hash(self) -> str:
        """Generate a verification hash for this evidence pack."""
        data = f"{self.id}|{self.migration_id}|{self.created_at}|{self.overall_status}"
        for status in self.domain_statuses:
            data += f"|{status.domain}:{status.status}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "migration_id": self.migration_id,
            "source_systems": self.source_systems,
            "target_system": self.target_system,
            "domain_statuses": [d.to_dict() for d in self.domain_statuses],
            "reconciliation_summary": {
                "total_checks": len(self.reconciliation_results),
                "passed": sum(1 for r in self.reconciliation_results if r.get("status") == "passed"),
                "failed": sum(1 for r in self.reconciliation_results if r.get("status") == "failed"),
            },
            "sample_verification_count": len(self.sample_verifications),
            "data_hashes": self.data_hashes,
            "overall_status": self.overall_status,
            "approval_status": self.approval_status,
            "approver": self.approver,
            "verification_hash": self.generate_hash(),
            "notes": self.notes,
        }

    def to_json(self) -> str:
        """Export evidence pack as JSON."""
        return json.dumps(self.to_dict(), indent=2)


class ReportGenerator:
    """
    Generates various reports for migration verification.
    """

    def __init__(self):
        self.evidence_packs: Dict[str, EvidencePack] = {}

    def create_evidence_pack(self, migration_id: str, source_systems: List[str],
                              target_system: str = "Cloud SIS") -> EvidencePack:
        """Create a new evidence pack for a migration."""
        pack = EvidencePack(
            id=f"EP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now(),
            migration_id=migration_id,
            source_systems=source_systems,
            target_system=target_system
        )
        self.evidence_packs[pack.id] = pack
        return pack

    def add_domain_status(self, pack_id: str, domain: str,
                          check_results: List[Dict[str, Any]]) -> DomainStatus:
        """Add domain status to an evidence pack."""
        pack = self.evidence_packs.get(pack_id)
        if not pack:
            raise ValueError(f"Evidence pack {pack_id} not found")

        passed = sum(1 for r in check_results if r.get("status") == "passed")
        failed = sum(1 for r in check_results if r.get("status") == "failed")
        total = len(check_results)

        if failed > 0:
            status = "failed"
        elif passed < total:
            status = "warning"
        else:
            status = "passed"

        issues = [
            r.get("message", "Unknown issue")
            for r in check_results
            if r.get("status") in ["failed", "warning"]
        ]

        domain_status = DomainStatus(
            domain=domain,
            status=status,
            checks_passed=passed,
            checks_total=total,
            issues=issues
        )

        pack.domain_statuses.append(domain_status)
        pack.reconciliation_results.extend(check_results)
        pack.calculate_overall_status()

        return domain_status

    def generate_reconciliation_report(self, check_results: List[Dict[str, Any]],
                                        source_name: str, target_name: str) -> Dict[str, Any]:
        """Generate a detailed reconciliation report."""
        passed = [r for r in check_results if r.get("status") == "passed"]
        failed = [r for r in check_results if r.get("status") == "failed"]
        warnings = [r for r in check_results if r.get("status") == "warning"]
        skipped = [r for r in check_results if r.get("status") == "skipped"]

        # Group by category
        by_category: Dict[str, List[Dict]] = {}
        for result in check_results:
            cat = result.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        return {
            "report_id": f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "source_system": source_name,
            "target_system": target_name,
            "summary": {
                "total_checks": len(check_results),
                "passed": len(passed),
                "failed": len(failed),
                "warnings": len(warnings),
                "skipped": len(skipped),
                "pass_rate": len(passed) / len(check_results) if check_results else 0,
                "overall_status": "PASSED" if len(failed) == 0 else "FAILED",
            },
            "by_category": {
                cat: {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.get("status") == "passed"),
                    "failed": sum(1 for r in results if r.get("status") == "failed"),
                }
                for cat, results in by_category.items()
            },
            "failures": failed,
            "warnings": warnings,
            "all_results": check_results,
        }

    def generate_acceptance_report(self, pack_id: str) -> Dict[str, Any]:
        """Generate an acceptance test report."""
        pack = self.evidence_packs.get(pack_id)
        if not pack:
            raise ValueError(f"Evidence pack {pack_id} not found")

        # Determine acceptance criteria results
        criteria = [
            {
                "id": "AC-001",
                "name": "Data Completeness",
                "description": "All source records migrated to target",
                "status": "passed" if pack.overall_status != "failed" else "failed",
                "evidence": "Count reconciliation checks"
            },
            {
                "id": "AC-002",
                "name": "Referential Integrity",
                "description": "All relationships maintained",
                "status": self._check_domain_status(pack, "referential"),
                "evidence": "Referential integrity checks"
            },
            {
                "id": "AC-003",
                "name": "Data Quality",
                "description": "Data quality standards met",
                "status": self._check_domain_status(pack, "completeness"),
                "evidence": "Completeness checks"
            },
            {
                "id": "AC-004",
                "name": "Data Integrity",
                "description": "Data not corrupted during migration",
                "status": self._check_domain_status(pack, "integrity"),
                "evidence": "Hash verification"
            },
        ]

        all_passed = all(c["status"] == "passed" for c in criteria)

        return {
            "report_id": f"ACC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "evidence_pack_id": pack_id,
            "generated_at": datetime.now().isoformat(),
            "migration_id": pack.migration_id,
            "acceptance_criteria": criteria,
            "all_criteria_met": all_passed,
            "recommendation": "APPROVED" if all_passed else "REQUIRES_REVIEW",
            "sign_off_required": not all_passed,
        }

    def _check_domain_status(self, pack: EvidencePack, category: str) -> str:
        """Check status of a specific category in the evidence pack."""
        relevant_results = [
            r for r in pack.reconciliation_results
            if r.get("category") == category
        ]
        if not relevant_results:
            return "skipped"
        failed = any(r.get("status") == "failed" for r in relevant_results)
        return "failed" if failed else "passed"

    def generate_domain_summary(self, pack_id: str) -> List[Dict[str, Any]]:
        """Generate a domain-by-domain summary."""
        pack = self.evidence_packs.get(pack_id)
        if not pack:
            return []

        domains = {
            "identity": {"name": "Identity & Relationships", "icon": "users"},
            "enrollment": {"name": "Enrollment & Calendar", "icon": "calendar"},
            "grades": {"name": "Grades & Transcripts", "icon": "graduation-cap"},
            "attendance": {"name": "Attendance", "icon": "clock"},
        }

        summary = []
        for domain_key, domain_info in domains.items():
            # Find domain status
            domain_status = next(
                (d for d in pack.domain_statuses if d.domain.lower() == domain_key),
                None
            )

            if domain_status:
                summary.append({
                    "domain": domain_key,
                    "name": domain_info["name"],
                    "icon": domain_info["icon"],
                    "status": domain_status.status,
                    "checks_passed": domain_status.checks_passed,
                    "checks_total": domain_status.checks_total,
                    "issues": domain_status.issues[:3],  # First 3 issues
                })
            else:
                summary.append({
                    "domain": domain_key,
                    "name": domain_info["name"],
                    "icon": domain_info["icon"],
                    "status": "pending",
                    "checks_passed": 0,
                    "checks_total": 0,
                    "issues": [],
                })

        return summary

    def export_to_json(self, pack_id: str) -> str:
        """Export complete evidence pack to JSON."""
        pack = self.evidence_packs.get(pack_id)
        if not pack:
            return json.dumps({"error": "Evidence pack not found"})
        return pack.to_json()

    def generate_summary_stats(self, pack_id: str) -> Dict[str, Any]:
        """Generate summary statistics for display."""
        pack = self.evidence_packs.get(pack_id)
        if not pack:
            return {}

        total_checks = len(pack.reconciliation_results)
        passed = sum(1 for r in pack.reconciliation_results if r.get("status") == "passed")
        failed = sum(1 for r in pack.reconciliation_results if r.get("status") == "failed")

        domains_passed = sum(1 for d in pack.domain_statuses if d.status == "passed")
        domains_total = len(pack.domain_statuses)

        return {
            "evidence_pack_id": pack_id,
            "overall_status": pack.overall_status,
            "checks": {
                "total": total_checks,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed / total_checks * 100):.1f}%" if total_checks > 0 else "N/A"
            },
            "domains": {
                "total": domains_total,
                "passed": domains_passed,
                "status_summary": {d.domain: d.status for d in pack.domain_statuses}
            },
            "ready_for_approval": pack.overall_status != "failed",
            "created_at": pack.created_at.isoformat(),
        }
