"""
Enrollment Processing Module
Based on DMaaS Playbook Section 1.1.2

Provides:
- Calendar Canonicalization: Day types, terms, sessions
- Enrollment Span Normalization: Resolve overlaps/gaps
- Term Crosswalk: Map legacy terms to canonical terms
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re


class TermType(Enum):
    """Types of academic terms."""
    YEAR = "year"
    SEMESTER = "semester"
    TRIMESTER = "trimester"
    QUARTER = "quarter"
    SUMMER = "summer"
    INTERSESSION = "intersession"


class DayType(Enum):
    """Types of school days."""
    INSTRUCTIONAL = "instructional"
    PROFESSIONAL_DEVELOPMENT = "professional_development"
    HOLIDAY = "holiday"
    WEATHER = "weather"
    BREAK = "break"
    EXAM = "exam"


class EnrollmentAction(Enum):
    """Actions to resolve enrollment issues."""
    KEEP = "keep"
    MERGE = "merge"
    EXTEND = "extend"
    TRUNCATE = "truncate"
    SPLIT = "split"
    DELETE = "delete"


@dataclass
class AcademicTerm:
    """Represents an academic term/session."""
    id: str
    name: str
    term_type: TermType
    start_date: date
    end_date: date
    school_year: str
    is_primary: bool = True
    parent_term_id: Optional[str] = None  # For nested terms (e.g., quarter within semester)

    def duration_days(self) -> int:
        """Calculate the duration in days."""
        return (self.end_date - self.start_date).days + 1

    def contains_date(self, check_date: date) -> bool:
        """Check if a date falls within this term."""
        return self.start_date <= check_date <= self.end_date

    def overlaps_with(self, other: 'AcademicTerm') -> bool:
        """Check if this term overlaps with another."""
        return self.start_date <= other.end_date and other.start_date <= self.end_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "term_type": self.term_type.value,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "school_year": self.school_year,
        }


@dataclass
class EnrollmentSpan:
    """Represents a student's enrollment period at a school."""
    id: str
    student_id: str
    school_id: str
    school_name: str
    grade_level: int
    start_date: date
    end_date: Optional[date] = None
    status: str = "active"
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    source_system: Optional[str] = None

    def is_active(self, as_of: date = None) -> bool:
        """Check if enrollment is active as of a given date."""
        check_date = as_of or date.today()
        if self.end_date:
            return self.start_date <= check_date <= self.end_date
        return self.start_date <= check_date

    def overlaps_with(self, other: 'EnrollmentSpan') -> Tuple[bool, int]:
        """
        Check if this enrollment overlaps with another.
        Returns (overlaps, overlap_days).
        """
        if self.end_date is None and other.end_date is None:
            # Both are ongoing - check if same school
            return self.school_id == other.school_id, 0

        self_end = self.end_date or date.today()
        other_end = other.end_date or date.today()

        if self.start_date <= other_end and other.start_date <= self_end:
            overlap_start = max(self.start_date, other.start_date)
            overlap_end = min(self_end, other_end)
            overlap_days = (overlap_end - overlap_start).days + 1
            return True, overlap_days

        return False, 0

    def gap_with(self, other: 'EnrollmentSpan') -> Tuple[bool, int]:
        """
        Check if there's a gap between this enrollment and another.
        Returns (has_gap, gap_days).
        """
        if self.end_date is None or other.end_date is None:
            return False, 0

        # Determine which comes first
        if self.end_date < other.start_date:
            gap_days = (other.start_date - self.end_date).days - 1
            return gap_days > 0, gap_days
        elif other.end_date < self.start_date:
            gap_days = (self.start_date - other.end_date).days - 1
            return gap_days > 0, gap_days

        return False, 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "school_id": self.school_id,
            "school_name": self.school_name,
            "grade_level": self.grade_level,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date) if self.end_date else None,
            "status": self.status,
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
        }


class CalendarNormalizer:
    """
    Normalizes calendar and term data from various sources.
    """

    # Common term name mappings
    TERM_MAPPINGS = {
        # Semesters
        "fall": ("Fall", TermType.SEMESTER),
        "fall semester": ("Fall", TermType.SEMESTER),
        "fall sem": ("Fall", TermType.SEMESTER),
        "autumn": ("Fall", TermType.SEMESTER),
        "spring": ("Spring", TermType.SEMESTER),
        "spring semester": ("Spring", TermType.SEMESTER),
        "spring sem": ("Spring", TermType.SEMESTER),
        # Quarters
        "q1": ("Quarter 1", TermType.QUARTER),
        "q2": ("Quarter 2", TermType.QUARTER),
        "q3": ("Quarter 3", TermType.QUARTER),
        "q4": ("Quarter 4", TermType.QUARTER),
        "quarter 1": ("Quarter 1", TermType.QUARTER),
        "quarter 2": ("Quarter 2", TermType.QUARTER),
        "quarter 3": ("Quarter 3", TermType.QUARTER),
        "quarter 4": ("Quarter 4", TermType.QUARTER),
        # Trimesters
        "t1": ("Trimester 1", TermType.TRIMESTER),
        "t2": ("Trimester 2", TermType.TRIMESTER),
        "t3": ("Trimester 3", TermType.TRIMESTER),
        "tri1": ("Trimester 1", TermType.TRIMESTER),
        "tri2": ("Trimester 2", TermType.TRIMESTER),
        "tri3": ("Trimester 3", TermType.TRIMESTER),
        # Full year
        "year": ("Full Year", TermType.YEAR),
        "full year": ("Full Year", TermType.YEAR),
        "annual": ("Full Year", TermType.YEAR),
        # Summer
        "summer": ("Summer", TermType.SUMMER),
        "summer session": ("Summer", TermType.SUMMER),
        "summer school": ("Summer", TermType.SUMMER),
    }

    def __init__(self):
        self.terms: Dict[str, AcademicTerm] = {}

    def normalize_term_name(self, term: str) -> Tuple[str, TermType]:
        """Normalize a term name to canonical form."""
        normalized = str(term).lower().strip()
        if normalized in self.TERM_MAPPINGS:
            return self.TERM_MAPPINGS[normalized]
        # Default
        return (term.title(), TermType.SEMESTER)

    def parse_school_year(self, year_str: str) -> str:
        """Parse various school year formats to standard YYYY-YYYY format."""
        # Handle various formats
        year_str = str(year_str).strip()

        # Already in correct format
        if re.match(r'^\d{4}-\d{4}$', year_str):
            return year_str

        # Single year (e.g., "2023") - assume it's the start year
        if re.match(r'^\d{4}$', year_str):
            start = int(year_str)
            return f"{start}-{start + 1}"

        # Two-digit year range (e.g., "23-24")
        match = re.match(r'^(\d{2})-(\d{2})$', year_str)
        if match:
            start, end = match.groups()
            century = "20" if int(start) < 50 else "19"
            return f"{century}{start}-{century}{end}"

        return year_str  # Return as-is if can't parse

    def create_standard_calendar(self, school_year: str,
                                  term_type: TermType = TermType.SEMESTER) -> List[AcademicTerm]:
        """
        Create a standard academic calendar for a school year.
        """
        years = school_year.split("-")
        start_year = int(years[0])
        end_year = int(years[1]) if len(years) > 1 else start_year + 1

        terms = []

        if term_type == TermType.SEMESTER:
            # Fall semester: Aug 15 - Dec 20
            terms.append(AcademicTerm(
                id=f"{school_year}-FALL",
                name="Fall",
                term_type=TermType.SEMESTER,
                start_date=date(start_year, 8, 15),
                end_date=date(start_year, 12, 20),
                school_year=school_year
            ))
            # Spring semester: Jan 5 - May 25
            terms.append(AcademicTerm(
                id=f"{school_year}-SPRING",
                name="Spring",
                term_type=TermType.SEMESTER,
                start_date=date(end_year, 1, 5),
                end_date=date(end_year, 5, 25),
                school_year=school_year
            ))

        elif term_type == TermType.QUARTER:
            dates = [
                ("Quarter 1", (8, 15), (10, 15)),
                ("Quarter 2", (10, 16), (12, 20)),
                ("Quarter 3", (1, 5), (3, 15)),
                ("Quarter 4", (3, 16), (5, 25)),
            ]
            for i, (name, (sm, sd), (em, ed)) in enumerate(dates):
                year = start_year if i < 2 else end_year
                terms.append(AcademicTerm(
                    id=f"{school_year}-Q{i + 1}",
                    name=name,
                    term_type=TermType.QUARTER,
                    start_date=date(year, sm, sd),
                    end_date=date(year, em, ed),
                    school_year=school_year
                ))

        for term in terms:
            self.terms[term.id] = term

        return terms

    def crosswalk_term(self, source_term: str, source_year: str,
                       target_calendar: List[AcademicTerm]) -> Optional[AcademicTerm]:
        """
        Map a source system term to a target calendar term.
        """
        canonical_name, _ = self.normalize_term_name(source_term)

        for term in target_calendar:
            if term.name.lower() == canonical_name.lower():
                return term

        # Fuzzy match
        source_lower = source_term.lower()
        for term in target_calendar:
            if source_lower in term.name.lower() or term.name.lower() in source_lower:
                return term

        return None


class EnrollmentProcessor:
    """
    Processes and normalizes enrollment data.
    """

    def __init__(self):
        self.enrollments: Dict[str, List[EnrollmentSpan]] = {}  # student_id -> enrollments
        self.issues: List[Dict[str, Any]] = []
        self.calendar = CalendarNormalizer()

    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse various date formats."""
        if not date_str or str(date_str).upper() in ["NULL", "N/A", ""]:
            return None

        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%B %d %Y",
            "%B %d, %Y",
            "%b %d %Y",
            "%b %d, %Y",
            "%B %dst %Y",
            "%B %dnd %Y",
            "%B %drd %Y",
            "%B %dth %Y",
            "%d %B %Y",
            "%Y%m%d",
        ]

        # Clean the date string
        date_str = str(date_str).strip()
        # Remove ordinal suffixes
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def add_enrollment(self, record: Dict[str, Any], source: str = "default") -> EnrollmentSpan:
        """Add an enrollment record."""
        student_id = str(record.get("student_id", ""))
        start_date = self.parse_date(record.get("start_date", ""))
        end_date = self.parse_date(record.get("end_date", ""))

        enrollment = EnrollmentSpan(
            id=str(record.get("enrollment_id", f"{student_id}-{source}")),
            student_id=student_id,
            school_id=str(record.get("school_id", "")),
            school_name=str(record.get("school_name", "")),
            grade_level=int(record.get("grade_level", 0)),
            start_date=start_date or date.today(),
            end_date=end_date,
            status=str(record.get("status", "Active")),
            entry_reason=record.get("entry_reason"),
            exit_reason=record.get("exit_reason"),
            source_system=source
        )

        if student_id not in self.enrollments:
            self.enrollments[student_id] = []
        self.enrollments[student_id].append(enrollment)

        return enrollment

    def find_overlaps(self, student_id: str) -> List[Tuple[EnrollmentSpan, EnrollmentSpan, int]]:
        """Find overlapping enrollments for a student."""
        overlaps = []
        enrollments = self.enrollments.get(student_id, [])

        for i, e1 in enumerate(enrollments):
            for e2 in enrollments[i + 1:]:
                overlaps_flag, days = e1.overlaps_with(e2)
                if overlaps_flag and days > 0:
                    overlaps.append((e1, e2, days))
                    self.issues.append({
                        "type": "overlap",
                        "student_id": student_id,
                        "enrollment1": e1.id,
                        "enrollment2": e2.id,
                        "overlap_days": days,
                    })

        return overlaps

    def find_gaps(self, student_id: str) -> List[Tuple[EnrollmentSpan, EnrollmentSpan, int]]:
        """Find gaps between enrollments for a student."""
        gaps = []
        enrollments = sorted(
            self.enrollments.get(student_id, []),
            key=lambda e: e.start_date
        )

        for i in range(len(enrollments) - 1):
            e1, e2 = enrollments[i], enrollments[i + 1]
            has_gap, gap_days = e1.gap_with(e2)
            if has_gap and gap_days > 5:  # Only flag gaps > 5 days
                gaps.append((e1, e2, gap_days))
                self.issues.append({
                    "type": "gap",
                    "student_id": student_id,
                    "enrollment1": e1.id,
                    "enrollment2": e2.id,
                    "gap_days": gap_days,
                })

        return gaps

    def normalize_enrollments(self, student_id: str) -> List[EnrollmentSpan]:
        """
        Normalize enrollments for a student by resolving overlaps.
        """
        enrollments = self.enrollments.get(student_id, [])
        if not enrollments:
            return []

        # Sort by start date
        sorted_enrollments = sorted(enrollments, key=lambda e: e.start_date)

        # Resolve overlaps
        resolved = []
        for enrollment in sorted_enrollments:
            if not resolved:
                resolved.append(enrollment)
                continue

            last = resolved[-1]
            overlaps, days = last.overlaps_with(enrollment)

            if overlaps and last.school_id == enrollment.school_id:
                # Same school - extend the previous enrollment
                if enrollment.end_date:
                    if last.end_date is None or enrollment.end_date > last.end_date:
                        last.end_date = enrollment.end_date
            else:
                resolved.append(enrollment)

        self.enrollments[student_id] = resolved
        return resolved

    def get_active_enrollment(self, student_id: str, as_of: date = None) -> Optional[EnrollmentSpan]:
        """Get the active enrollment for a student as of a date."""
        check_date = as_of or date.today()
        enrollments = self.enrollments.get(student_id, [])

        for enrollment in enrollments:
            if enrollment.is_active(check_date):
                return enrollment

        return None

    def get_enrollment_history(self, student_id: str) -> List[Dict[str, Any]]:
        """Get the full enrollment history for a student."""
        enrollments = self.enrollments.get(student_id, [])
        sorted_enrollments = sorted(enrollments, key=lambda e: e.start_date)
        return [e.to_dict() for e in sorted_enrollments]

    def get_stats(self) -> Dict[str, Any]:
        """Get enrollment processing statistics."""
        total_enrollments = sum(len(e) for e in self.enrollments.values())
        return {
            "total_students": len(self.enrollments),
            "total_enrollments": total_enrollments,
            "issues_found": len(self.issues),
            "overlaps": sum(1 for i in self.issues if i["type"] == "overlap"),
            "gaps": sum(1 for i in self.issues if i["type"] == "gap"),
        }
