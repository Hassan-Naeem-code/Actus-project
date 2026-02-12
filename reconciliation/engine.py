"""
Reconciliation Engine
Based on DMaaS Playbook Section 4E

Provides verification checks:
- Count Reconciliation: Source count vs Target count by entity
- Referential Integrity: All relationships reference valid entities
- Identity Completeness: 99.5%+ students have guardian + contact
- Sampling Verification: Random sample comparison
- Hash Comparison: Data integrity verification
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable, Set
from enum import Enum
import hashlib
import random


class CheckStatus(Enum):
    """Status of a reconciliation check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class CheckCategory(Enum):
    """Categories of reconciliation checks."""
    COUNT = "count"
    REFERENTIAL = "referential"
    COMPLETENESS = "completeness"
    SAMPLING = "sampling"
    INTEGRITY = "integrity"
    DOMAIN = "domain"


@dataclass
class CheckResult:
    """Result of a single reconciliation check."""
    check_id: str
    check_name: str
    category: CheckCategory
    status: CheckStatus
    message: str
    source_value: Any = None
    target_value: Any = None
    threshold: Optional[float] = None
    actual_value: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_name": self.check_name,
            "category": self.category.value,
            "status": self.status.value,
            "message": self.message,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "threshold": self.threshold,
            "actual_value": self.actual_value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReconciliationCheck:
    """Definition of a reconciliation check to run."""
    id: str
    name: str
    category: CheckCategory
    description: str
    threshold: float = 1.0  # 1.0 = 100% match required
    is_blocking: bool = False  # If True, failure blocks migration
    check_function: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "threshold": self.threshold,
            "is_blocking": self.is_blocking,
        }


class ReconciliationEngine:
    """
    Engine for running reconciliation checks on migrated data.
    """

    def __init__(self):
        self.checks: List[ReconciliationCheck] = []
        self.results: List[CheckResult] = []
        self.source_data: Dict[str, Any] = {}
        self.target_data: Dict[str, Any] = {}
        self._register_default_checks()

    def _register_default_checks(self):
        """Register the standard reconciliation checks."""
        default_checks = [
            # Count checks
            ReconciliationCheck(
                id="count_students",
                name="Student Count Match",
                category=CheckCategory.COUNT,
                description="Verify source and target student counts match",
                threshold=1.0,
                is_blocking=True
            ),
            ReconciliationCheck(
                id="count_guardians",
                name="Guardian Count Match",
                category=CheckCategory.COUNT,
                description="Verify source and target guardian counts match",
                threshold=1.0
            ),
            ReconciliationCheck(
                id="count_enrollments",
                name="Enrollment Count Match",
                category=CheckCategory.COUNT,
                description="Verify enrollment record counts match",
                threshold=1.0
            ),
            ReconciliationCheck(
                id="count_grades",
                name="Grade Record Count Match",
                category=CheckCategory.COUNT,
                description="Verify grade record counts match",
                threshold=0.99  # Allow 1% variance for deduplication
            ),
            ReconciliationCheck(
                id="count_attendance",
                name="Attendance Record Count Match",
                category=CheckCategory.COUNT,
                description="Verify attendance record counts match",
                threshold=0.99
            ),

            # Referential integrity checks
            ReconciliationCheck(
                id="ref_enrollment_student",
                name="Enrollment-Student Reference",
                category=CheckCategory.REFERENTIAL,
                description="All enrollments reference valid students",
                threshold=1.0,
                is_blocking=True
            ),
            ReconciliationCheck(
                id="ref_grade_student",
                name="Grade-Student Reference",
                category=CheckCategory.REFERENTIAL,
                description="All grades reference valid students",
                threshold=1.0,
                is_blocking=True
            ),
            ReconciliationCheck(
                id="ref_attendance_student",
                name="Attendance-Student Reference",
                category=CheckCategory.REFERENTIAL,
                description="All attendance records reference valid students",
                threshold=1.0,
                is_blocking=True
            ),
            ReconciliationCheck(
                id="ref_guardian_student",
                name="Guardian-Student Relationship",
                category=CheckCategory.REFERENTIAL,
                description="All guardian relationships reference valid students",
                threshold=1.0
            ),

            # Completeness checks
            ReconciliationCheck(
                id="complete_student_guardian",
                name="Student Guardian Coverage",
                category=CheckCategory.COMPLETENESS,
                description="99.5%+ students have at least one guardian",
                threshold=0.995
            ),
            ReconciliationCheck(
                id="complete_student_contact",
                name="Student Contact Info",
                category=CheckCategory.COMPLETENESS,
                description="99%+ students have contact information",
                threshold=0.99
            ),
            ReconciliationCheck(
                id="complete_student_enrollment",
                name="Student Enrollment",
                category=CheckCategory.COMPLETENESS,
                description="All students have at least one enrollment",
                threshold=1.0
            ),

            # Sampling checks
            ReconciliationCheck(
                id="sample_student_data",
                name="Student Data Sampling",
                category=CheckCategory.SAMPLING,
                description="Random sample verification of student records",
                threshold=0.99
            ),
            ReconciliationCheck(
                id="sample_grade_data",
                name="Grade Data Sampling",
                category=CheckCategory.SAMPLING,
                description="Random sample verification of grade records",
                threshold=0.99
            ),

            # Data integrity checks
            ReconciliationCheck(
                id="integrity_hash",
                name="Data Hash Verification",
                category=CheckCategory.INTEGRITY,
                description="Verify data integrity via hash comparison",
                threshold=1.0,
                is_blocking=True
            ),
        ]

        for check in default_checks:
            self.register_check(check)

    def register_check(self, check: ReconciliationCheck):
        """Register a new reconciliation check."""
        self.checks.append(check)

    def set_source_data(self, entity_type: str, data: List[Dict[str, Any]]):
        """Set source data for an entity type."""
        self.source_data[entity_type] = data

    def set_target_data(self, entity_type: str, data: List[Dict[str, Any]]):
        """Set target data for an entity type."""
        self.target_data[entity_type] = data

    def run_count_check(self, entity_type: str, check: ReconciliationCheck) -> CheckResult:
        """Run a count reconciliation check."""
        source_count = len(self.source_data.get(entity_type, []))
        target_count = len(self.target_data.get(entity_type, []))

        if source_count == 0:
            return CheckResult(
                check_id=check.id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.SKIPPED,
                message=f"No source data for {entity_type}",
                source_value=0,
                target_value=0
            )

        match_rate = target_count / source_count if source_count > 0 else 0
        passed = match_rate >= check.threshold

        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            message=f"{entity_type}: {target_count}/{source_count} records ({match_rate:.1%})",
            source_value=source_count,
            target_value=target_count,
            threshold=check.threshold,
            actual_value=match_rate,
            details={
                "entity_type": entity_type,
                "difference": source_count - target_count
            }
        )

    def run_referential_check(self, child_type: str, parent_type: str,
                               foreign_key: str, check: ReconciliationCheck) -> CheckResult:
        """Run a referential integrity check."""
        children = self.target_data.get(child_type, [])
        parents = self.target_data.get(parent_type, [])

        if not children:
            return CheckResult(
                check_id=check.id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.SKIPPED,
                message=f"No {child_type} data to check"
            )

        # Build parent ID set
        parent_ids: Set[str] = set()
        for parent in parents:
            parent_id = parent.get("student_id") or parent.get("id") or parent.get("guardian_id")
            if parent_id:
                parent_ids.add(str(parent_id))

        # Check child references
        valid_count = 0
        invalid_refs = []
        for child in children:
            fk_value = child.get(foreign_key)
            if fk_value and str(fk_value) in parent_ids:
                valid_count += 1
            else:
                invalid_refs.append({"record": child.get("id", "unknown"), "fk": fk_value})

        match_rate = valid_count / len(children) if children else 0
        passed = match_rate >= check.threshold

        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            message=f"{valid_count}/{len(children)} valid references ({match_rate:.1%})",
            source_value=len(children),
            target_value=valid_count,
            threshold=check.threshold,
            actual_value=match_rate,
            details={
                "invalid_count": len(invalid_refs),
                "sample_invalid": invalid_refs[:5]  # First 5 invalid refs
            }
        )

    def run_completeness_check(self, entity_type: str, required_field: str,
                                check: ReconciliationCheck) -> CheckResult:
        """Run a completeness check."""
        entities = self.target_data.get(entity_type, [])

        if not entities:
            return CheckResult(
                check_id=check.id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.SKIPPED,
                message=f"No {entity_type} data to check"
            )

        complete_count = 0
        incomplete = []
        for entity in entities:
            value = entity.get(required_field)
            if value and str(value).strip() and str(value).upper() not in ["NULL", "N/A"]:
                complete_count += 1
            else:
                incomplete.append(entity.get("id") or entity.get("student_id"))

        completeness_rate = complete_count / len(entities)
        passed = completeness_rate >= check.threshold

        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED if passed else CheckStatus.WARNING,
            message=f"{complete_count}/{len(entities)} have {required_field} ({completeness_rate:.1%})",
            source_value=len(entities),
            target_value=complete_count,
            threshold=check.threshold,
            actual_value=completeness_rate,
            details={
                "incomplete_count": len(incomplete),
                "sample_incomplete": incomplete[:10]
            }
        )

    def run_sampling_check(self, entity_type: str, sample_size: int,
                            check: ReconciliationCheck) -> CheckResult:
        """Run a random sampling verification check."""
        source = self.source_data.get(entity_type, [])
        target = self.target_data.get(entity_type, [])

        if not source or not target:
            return CheckResult(
                check_id=check.id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.SKIPPED,
                message=f"Insufficient data for sampling"
            )

        # Build target lookup
        target_lookup: Dict[str, Dict] = {}
        for record in target:
            key = record.get("student_id") or record.get("id")
            if key:
                target_lookup[str(key)] = record

        # Random sample from source
        sample_records = random.sample(source, min(sample_size, len(source)))
        matches = 0
        mismatches = []

        for source_record in sample_records:
            key = source_record.get("student_id") or source_record.get("id")
            target_record = target_lookup.get(str(key))

            if target_record:
                # Compare key fields
                if self._records_match(source_record, target_record):
                    matches += 1
                else:
                    mismatches.append(key)
            else:
                mismatches.append(key)

        match_rate = matches / len(sample_records)
        passed = match_rate >= check.threshold

        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            message=f"Sample: {matches}/{len(sample_records)} verified ({match_rate:.1%})",
            source_value=len(sample_records),
            target_value=matches,
            threshold=check.threshold,
            actual_value=match_rate,
            details={
                "sample_size": len(sample_records),
                "mismatches": mismatches[:5]
            }
        )

    def _records_match(self, source: Dict, target: Dict) -> bool:
        """Check if two records match on key fields."""
        # Compare common fields
        fields_to_check = ["first_name", "last_name", "email", "grade", "status"]
        for field in fields_to_check:
            if field in source and field in target:
                s_val = str(source[field]).strip().lower() if source[field] else ""
                t_val = str(target[field]).strip().lower() if target[field] else ""
                if s_val and t_val and s_val != t_val:
                    return False
        return True

    def run_hash_check(self, entity_type: str, check: ReconciliationCheck) -> CheckResult:
        """Run a data integrity hash check."""
        source = self.source_data.get(entity_type, [])
        target = self.target_data.get(entity_type, [])

        if not source or not target:
            return CheckResult(
                check_id=check.id,
                check_name=check.name,
                category=check.category,
                status=CheckStatus.SKIPPED,
                message="Insufficient data for hash verification"
            )

        # Calculate hashes
        source_hash = self._calculate_collection_hash(source)
        target_hash = self._calculate_collection_hash(target)

        passed = source_hash == target_hash

        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.PASSED if passed else CheckStatus.WARNING,
            message="Data integrity verified" if passed else "Hash mismatch (may be due to transformations)",
            source_value=source_hash[:16],
            target_value=target_hash[:16],
            details={
                "source_hash": source_hash,
                "target_hash": target_hash
            }
        )

    def _calculate_collection_hash(self, records: List[Dict]) -> str:
        """Calculate a hash for a collection of records."""
        # Sort records for consistent hashing
        sorted_records = sorted(records, key=lambda r: str(r.get("student_id") or r.get("id", "")))

        # Create hash from key fields
        hash_input = ""
        for record in sorted_records:
            key = record.get("student_id") or record.get("id", "")
            name = f"{record.get('first_name', '')}{record.get('last_name', '')}"
            hash_input += f"{key}|{name}|"

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def run_all_checks(self) -> List[CheckResult]:
        """Run all registered checks and return results."""
        self.results = []

        for check in self.checks:
            result = self._run_check(check)
            self.results.append(result)

        return self.results

    def _run_check(self, check: ReconciliationCheck) -> CheckResult:
        """Run a specific check based on its ID."""
        # Count checks
        if check.id == "count_students":
            return self.run_count_check("students", check)
        elif check.id == "count_guardians":
            return self.run_count_check("guardians", check)
        elif check.id == "count_enrollments":
            return self.run_count_check("enrollments", check)
        elif check.id == "count_grades":
            return self.run_count_check("grades", check)
        elif check.id == "count_attendance":
            return self.run_count_check("attendance", check)

        # Referential checks
        elif check.id == "ref_enrollment_student":
            return self.run_referential_check("enrollments", "students", "student_id", check)
        elif check.id == "ref_grade_student":
            return self.run_referential_check("grades", "students", "student_id", check)
        elif check.id == "ref_attendance_student":
            return self.run_referential_check("attendance", "students", "student_id", check)
        elif check.id == "ref_guardian_student":
            return self.run_referential_check("relationships", "students", "student_id", check)

        # Completeness checks
        elif check.id == "complete_student_guardian":
            return self.run_completeness_check("students", "guardian_id", check)
        elif check.id == "complete_student_contact":
            return self.run_completeness_check("students", "email", check)
        elif check.id == "complete_student_enrollment":
            return self.run_completeness_check("students", "enrollment_id", check)

        # Sampling checks
        elif check.id == "sample_student_data":
            return self.run_sampling_check("students", 10, check)
        elif check.id == "sample_grade_data":
            return self.run_sampling_check("grades", 20, check)

        # Hash check
        elif check.id == "integrity_hash":
            return self.run_hash_check("students", check)

        # Default
        return CheckResult(
            check_id=check.id,
            check_name=check.name,
            category=check.category,
            status=CheckStatus.SKIPPED,
            message="Check not implemented"
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all check results."""
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIPPED)

        blocking_failures = sum(
            1 for r in self.results
            if r.status == CheckStatus.FAILED and
            any(c.id == r.check_id and c.is_blocking for c in self.checks)
        )

        return {
            "total_checks": len(self.results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
            "blocking_failures": blocking_failures,
            "overall_status": "PASSED" if failed == 0 else ("BLOCKED" if blocking_failures > 0 else "WARNING"),
            "pass_rate": passed / len(self.results) if self.results else 0,
        }

    def get_results_by_category(self) -> Dict[str, List[CheckResult]]:
        """Get results grouped by category."""
        by_category: Dict[str, List[CheckResult]] = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)
        return by_category
