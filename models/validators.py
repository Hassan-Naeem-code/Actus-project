"""
Data Validation Rules Engine
Based on DMaaS Playbook data quality requirements

Provides validation for:
- Required fields
- Data formats (email, phone, dates)
- Business rules (valid grade levels, GPA ranges)
- Referential integrity
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import re


class ValidationSeverity(Enum):
    """Severity levels for validation results."""
    ERROR = "error"  # Must be fixed before migration
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None
    suggested_fix: Optional[str] = None
    rule_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "value": str(self.value) if self.value else None,
            "suggested_fix": self.suggested_fix,
            "rule_id": self.rule_id,
        }


@dataclass
class ValidationReport:
    """Complete validation report for a record or dataset."""
    record_id: str
    record_type: str
    results: List[ValidationResult] = field(default_factory=list)
    is_valid: bool = True
    timestamp: datetime = field(default_factory=datetime.now)

    def add_result(self, result: ValidationResult):
        """Add a validation result to the report."""
        self.results.append(result)
        if result.severity == ValidationSeverity.ERROR:
            self.is_valid = False

    def error_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.ERROR)

    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.severity == ValidationSeverity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "is_valid": self.is_valid,
            "error_count": self.error_count(),
            "warning_count": self.warning_count(),
            "results": [r.to_dict() for r in self.results],
        }


class DataValidator:
    """
    Validation engine for school data.
    Provides pre-built rules and custom rule support.
    """

    # Email regex pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Phone patterns (various formats)
    PHONE_PATTERNS = [
        re.compile(r'^\d{3}-\d{3}-\d{4}$'),  # 555-123-4567
        re.compile(r'^\(\d{3}\)\s?\d{3}-\d{4}$'),  # (555) 123-4567
        re.compile(r'^\d{3}\.\d{3}\.\d{4}$'),  # 555.123.4567
        re.compile(r'^\d{10}$'),  # 5551234567
    ]

    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%b %d, %Y",
    ]

    def __init__(self):
        self.custom_rules: List[Callable] = []

    def add_custom_rule(self, rule: Callable):
        """Add a custom validation rule."""
        self.custom_rules.append(rule)

    def validate_email(self, email: str, field_name: str = "email") -> Optional[ValidationResult]:
        """Validate email format."""
        if not email or email.upper() in ["NULL", "N/A", ""]:
            return ValidationResult(
                field=field_name,
                message="Missing email address",
                severity=ValidationSeverity.WARNING,
                value=email,
                suggested_fix="Add valid email address",
                rule_id="EMAIL_MISSING"
            )

        # Check for common typos
        if email.count("@") > 1:
            return ValidationResult(
                field=field_name,
                message="Invalid email: multiple @ symbols",
                severity=ValidationSeverity.ERROR,
                value=email,
                suggested_fix=email.replace("@@", "@"),
                rule_id="EMAIL_DOUBLE_AT"
            )

        if not self.EMAIL_PATTERN.match(email):
            return ValidationResult(
                field=field_name,
                message="Invalid email format",
                severity=ValidationSeverity.ERROR,
                value=email,
                rule_id="EMAIL_INVALID_FORMAT"
            )

        return None

    def validate_phone(self, phone: str, field_name: str = "phone") -> Optional[ValidationResult]:
        """Validate phone number format."""
        if not phone or phone.upper() in ["NULL", "N/A", ""]:
            return ValidationResult(
                field=field_name,
                message="Missing phone number",
                severity=ValidationSeverity.WARNING,
                value=phone,
                rule_id="PHONE_MISSING"
            )

        # Clean phone number for validation
        cleaned = re.sub(r'[^\d]', '', str(phone))

        if len(cleaned) < 10:
            return ValidationResult(
                field=field_name,
                message="Phone number too short",
                severity=ValidationSeverity.ERROR,
                value=phone,
                suggested_fix=f"Expected 10 digits, got {len(cleaned)}",
                rule_id="PHONE_TOO_SHORT"
            )

        return None

    def validate_grade_level(self, grade: Any, field_name: str = "grade_level") -> Optional[ValidationResult]:
        """Validate grade level is within expected range."""
        try:
            grade_int = int(grade)
            if grade_int < -1 or grade_int > 12:  # -1 for Pre-K, 0 for K
                return ValidationResult(
                    field=field_name,
                    message=f"Invalid grade level: {grade_int}",
                    severity=ValidationSeverity.ERROR,
                    value=grade,
                    suggested_fix="Grade should be -1 (Pre-K) to 12",
                    rule_id="GRADE_OUT_OF_RANGE"
                )
        except (ValueError, TypeError):
            return ValidationResult(
                field=field_name,
                message=f"Non-numeric grade level: {grade}",
                severity=ValidationSeverity.ERROR,
                value=grade,
                rule_id="GRADE_NOT_NUMERIC"
            )
        return None

    def validate_gpa(self, gpa: Any, field_name: str = "gpa") -> Optional[ValidationResult]:
        """Validate GPA is within expected range."""
        if gpa is None or str(gpa).upper() in ["NULL", "N/A", ""]:
            return ValidationResult(
                field=field_name,
                message="Missing GPA",
                severity=ValidationSeverity.WARNING,
                value=gpa,
                rule_id="GPA_MISSING"
            )

        try:
            gpa_float = float(gpa)
            if gpa_float < 0:
                return ValidationResult(
                    field=field_name,
                    message=f"Negative GPA: {gpa_float}",
                    severity=ValidationSeverity.ERROR,
                    value=gpa,
                    suggested_fix="Replace with valid GPA (0.0-4.0)",
                    rule_id="GPA_NEGATIVE"
                )
            if gpa_float > 5.0:  # Allow up to 5.0 for weighted GPAs
                return ValidationResult(
                    field=field_name,
                    message=f"GPA exceeds maximum: {gpa_float}",
                    severity=ValidationSeverity.ERROR,
                    value=gpa,
                    suggested_fix="Maximum GPA is typically 4.0 (or 5.0 weighted)",
                    rule_id="GPA_TOO_HIGH"
                )
        except (ValueError, TypeError):
            return ValidationResult(
                field=field_name,
                message=f"Non-numeric GPA: {gpa}",
                severity=ValidationSeverity.ERROR,
                value=gpa,
                rule_id="GPA_NOT_NUMERIC"
            )
        return None

    def validate_date(self, date_str: str, field_name: str = "date") -> Optional[ValidationResult]:
        """Validate and parse date string."""
        if not date_str or str(date_str).upper() in ["NULL", "N/A", ""]:
            return ValidationResult(
                field=field_name,
                message="Missing date",
                severity=ValidationSeverity.WARNING,
                value=date_str,
                rule_id="DATE_MISSING"
            )

        # Try each date format
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(str(date_str).strip(), fmt)
                # Check for reasonable date range
                if parsed.year < 1900 or parsed.year > 2100:
                    return ValidationResult(
                        field=field_name,
                        message=f"Date year out of range: {parsed.year}",
                        severity=ValidationSeverity.ERROR,
                        value=date_str,
                        rule_id="DATE_YEAR_INVALID"
                    )
                return None
            except ValueError:
                continue

        return ValidationResult(
            field=field_name,
            message=f"Unrecognized date format: {date_str}",
            severity=ValidationSeverity.ERROR,
            value=date_str,
            suggested_fix="Use YYYY-MM-DD format",
            rule_id="DATE_INVALID_FORMAT"
        )

    def validate_required(self, value: Any, field_name: str) -> Optional[ValidationResult]:
        """Check if a required field has a value."""
        if value is None or str(value).strip() == "" or str(value).upper() in ["NULL", "N/A"]:
            return ValidationResult(
                field=field_name,
                message=f"Required field missing: {field_name}",
                severity=ValidationSeverity.ERROR,
                value=value,
                rule_id="REQUIRED_MISSING"
            )
        return None

    def validate_name(self, name: str, field_name: str = "name") -> Optional[ValidationResult]:
        """Validate name field for common issues."""
        if not name or str(name).strip() == "":
            return ValidationResult(
                field=field_name,
                message="Missing name",
                severity=ValidationSeverity.ERROR,
                value=name,
                rule_id="NAME_MISSING"
            )

        cleaned = str(name).strip()

        # Check for excessive whitespace
        if "  " in cleaned or cleaned != name:
            return ValidationResult(
                field=field_name,
                message="Name has whitespace issues",
                severity=ValidationSeverity.WARNING,
                value=name,
                suggested_fix=cleaned,
                rule_id="NAME_WHITESPACE"
            )

        # Check for inconsistent casing
        if cleaned.isupper() or cleaned.islower():
            return ValidationResult(
                field=field_name,
                message="Name casing may need normalization",
                severity=ValidationSeverity.INFO,
                value=name,
                suggested_fix=cleaned.title(),
                rule_id="NAME_CASING"
            )

        return None

    def validate_student_record(self, record: Dict[str, Any]) -> ValidationReport:
        """Validate a complete student record."""
        report = ValidationReport(
            record_id=str(record.get("student_id", "unknown")),
            record_type="student"
        )

        # Required fields
        for field in ["student_id", "first_name", "last_name"]:
            result = self.validate_required(record.get(field), field)
            if result:
                report.add_result(result)

        # Name validations
        if record.get("first_name"):
            result = self.validate_name(record["first_name"], "first_name")
            if result:
                report.add_result(result)

        if record.get("last_name"):
            result = self.validate_name(record["last_name"], "last_name")
            if result:
                report.add_result(result)

        # Email validation
        if record.get("email"):
            result = self.validate_email(record["email"])
            if result:
                report.add_result(result)

        # Phone validation
        if record.get("phone"):
            result = self.validate_phone(record["phone"])
            if result:
                report.add_result(result)

        # Grade level validation
        if record.get("grade") is not None:
            result = self.validate_grade_level(record["grade"], "grade")
            if result:
                report.add_result(result)

        # GPA validation
        if record.get("gpa") is not None:
            result = self.validate_gpa(record["gpa"])
            if result:
                report.add_result(result)

        # Date validation
        if record.get("enrollment_date"):
            result = self.validate_date(record["enrollment_date"], "enrollment_date")
            if result:
                report.add_result(result)

        return report

    def validate_guardian_record(self, record: Dict[str, Any]) -> ValidationReport:
        """Validate a guardian record."""
        report = ValidationReport(
            record_id=str(record.get("guardian_id", "unknown")),
            record_type="guardian"
        )

        # Required fields
        for field in ["guardian_id", "first_name", "last_name"]:
            result = self.validate_required(record.get(field), field)
            if result:
                report.add_result(result)

        # Contact info
        if record.get("email"):
            result = self.validate_email(record["email"])
            if result:
                report.add_result(result)

        if record.get("phone"):
            result = self.validate_phone(record["phone"])
            if result:
                report.add_result(result)

        # Must have at least one student linked
        if not record.get("student_ids"):
            report.add_result(ValidationResult(
                field="student_ids",
                message="Guardian has no linked students",
                severity=ValidationSeverity.WARNING,
                rule_id="GUARDIAN_NO_STUDENTS"
            ))

        return report

    def validate_enrollment_record(self, record: Dict[str, Any]) -> ValidationReport:
        """Validate an enrollment record."""
        report = ValidationReport(
            record_id=str(record.get("enrollment_id", "unknown")),
            record_type="enrollment"
        )

        # Required fields
        for field in ["enrollment_id", "student_id", "school_id", "start_date"]:
            result = self.validate_required(record.get(field), field)
            if result:
                report.add_result(result)

        # Date validations
        if record.get("start_date"):
            result = self.validate_date(record["start_date"], "start_date")
            if result:
                report.add_result(result)

        if record.get("end_date"):
            result = self.validate_date(record["end_date"], "end_date")
            if result:
                report.add_result(result)

        # Grade level
        if record.get("grade_level") is not None:
            result = self.validate_grade_level(record["grade_level"], "grade_level")
            if result:
                report.add_result(result)

        return report

    def validate_attendance_record(self, record: Dict[str, Any]) -> ValidationReport:
        """Validate an attendance record."""
        report = ValidationReport(
            record_id=str(record.get("ID", "unknown")),
            record_type="attendance"
        )

        # Required fields
        for field in ["StudentID", "Date", "Status"]:
            result = self.validate_required(record.get(field), field)
            if result:
                report.add_result(result)

        # Date validation
        if record.get("Date"):
            result = self.validate_date(record["Date"], "Date")
            if result:
                report.add_result(result)

        return report

    def validate_grade_record(self, record: Dict[str, Any]) -> ValidationReport:
        """Validate a grade/transcript record."""
        report = ValidationReport(
            record_id=f"{record.get('STUDENT_ID', 'unknown')}-{record.get('COURSE_CODE', 'unknown')}",
            record_type="grade"
        )

        # Required fields
        for field in ["STUDENT_ID", "COURSE_CODE", "COURSE_NAME"]:
            result = self.validate_required(record.get(field), field)
            if result:
                report.add_result(result)

        # Grade validation
        grade = record.get("GRADE")
        if grade and str(grade).strip():
            valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-",
                           "D+", "D", "D-", "F", "I", "W", "P", "NP"]
            if str(grade).upper().strip() not in valid_grades:
                report.add_result(ValidationResult(
                    field="GRADE",
                    message=f"Non-standard grade: {grade}",
                    severity=ValidationSeverity.WARNING,
                    value=grade,
                    rule_id="GRADE_NONSTANDARD"
                ))

        return report
