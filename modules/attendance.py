"""
Attendance Processing Module
Based on DMaaS Playbook Section 1.1.5

Provides:
- Code Taxonomy: Map varied codes (P/PRESENT/Present -> Present)
- Daily/Period Mapping: Normalize attendance events
- Aggregate Verification: Validate totals match
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any, Set
from enum import Enum
import re


class AttendanceStatus(Enum):
    """Canonical attendance status codes."""
    PRESENT = "Present"
    ABSENT = "Absent"
    TARDY = "Tardy"
    EXCUSED = "Excused"
    UNEXCUSED = "Unexcused"
    REMOTE = "Remote"
    EARLY_DEPARTURE = "Early Departure"
    HALF_DAY = "Half Day"


class AttendanceType(Enum):
    """Type of attendance record."""
    DAILY = "daily"
    PERIOD = "period"
    COURSE = "course"


@dataclass
class AttendanceRecord:
    """A single attendance record."""
    id: str
    student_id: str
    date: date
    status: AttendanceStatus
    attendance_type: AttendanceType = AttendanceType.DAILY
    period: Optional[int] = None
    section_id: Optional[str] = None
    teacher_name: Optional[str] = None
    notes: Optional[str] = None
    source_code: Optional[str] = None  # Original code from source
    source_system: Optional[str] = None

    def is_present(self) -> bool:
        """Check if status indicates presence."""
        return self.status in [AttendanceStatus.PRESENT, AttendanceStatus.TARDY,
                               AttendanceStatus.REMOTE, AttendanceStatus.HALF_DAY]

    def is_absent(self) -> bool:
        """Check if status indicates absence."""
        return self.status in [AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED,
                               AttendanceStatus.UNEXCUSED]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "date": str(self.date),
            "status": self.status.value,
            "attendance_type": self.attendance_type.value,
            "period": self.period,
            "teacher_name": self.teacher_name,
            "notes": self.notes,
            "source_code": self.source_code,
        }


@dataclass
class DailyAttendanceSummary:
    """Summary of a student's attendance for a single day."""
    student_id: str
    date: date
    periods_present: int = 0
    periods_absent: int = 0
    periods_tardy: int = 0
    total_periods: int = 0
    daily_status: AttendanceStatus = AttendanceStatus.PRESENT
    period_records: List[AttendanceRecord] = field(default_factory=list)

    def calculate_daily_status(self) -> AttendanceStatus:
        """Calculate overall daily status from period records."""
        if not self.period_records:
            return self.daily_status

        self.total_periods = len(self.period_records)
        self.periods_present = sum(1 for r in self.period_records if r.is_present())
        self.periods_absent = sum(1 for r in self.period_records if r.is_absent())
        self.periods_tardy = sum(1 for r in self.period_records
                                  if r.status == AttendanceStatus.TARDY)

        # Determine daily status
        if self.periods_absent == self.total_periods:
            self.daily_status = AttendanceStatus.ABSENT
        elif self.periods_absent > self.total_periods / 2:
            self.daily_status = AttendanceStatus.HALF_DAY
        elif self.periods_tardy > 0 and self.periods_absent == 0:
            self.daily_status = AttendanceStatus.TARDY
        else:
            self.daily_status = AttendanceStatus.PRESENT

        return self.daily_status


@dataclass
class AttendanceAggregate:
    """Aggregate attendance statistics for a student."""
    student_id: str
    start_date: date
    end_date: date
    days_present: int = 0
    days_absent: int = 0
    days_tardy: int = 0
    days_excused: int = 0
    days_unexcused: int = 0
    total_days: int = 0
    attendance_rate: float = 0.0

    def calculate_rate(self) -> float:
        """Calculate attendance rate as percentage."""
        if self.total_days > 0:
            self.attendance_rate = round(
                (self.days_present + self.days_tardy) / self.total_days * 100, 2
            )
        return self.attendance_rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "days_present": self.days_present,
            "days_absent": self.days_absent,
            "days_tardy": self.days_tardy,
            "total_days": self.total_days,
            "attendance_rate": self.attendance_rate,
        }


class AttendanceCodeMapper:
    """
    Maps various attendance codes to canonical status values.
    """

    # Code mappings from various systems
    CODE_MAPPINGS: Dict[str, AttendanceStatus] = {
        # Present variations
        "p": AttendanceStatus.PRESENT,
        "present": AttendanceStatus.PRESENT,
        "pres": AttendanceStatus.PRESENT,
        "pr": AttendanceStatus.PRESENT,
        "1": AttendanceStatus.PRESENT,
        "y": AttendanceStatus.PRESENT,
        "yes": AttendanceStatus.PRESENT,
        "in": AttendanceStatus.PRESENT,
        # Absent variations
        "a": AttendanceStatus.ABSENT,
        "absent": AttendanceStatus.ABSENT,
        "abs": AttendanceStatus.ABSENT,
        "ab": AttendanceStatus.ABSENT,
        "0": AttendanceStatus.ABSENT,
        "n": AttendanceStatus.ABSENT,
        "no": AttendanceStatus.ABSENT,
        "out": AttendanceStatus.ABSENT,
        # Tardy variations
        "t": AttendanceStatus.TARDY,
        "tardy": AttendanceStatus.TARDY,
        "late": AttendanceStatus.TARDY,
        "l": AttendanceStatus.TARDY,
        "lt": AttendanceStatus.TARDY,
        # Excused variations
        "e": AttendanceStatus.EXCUSED,
        "excused": AttendanceStatus.EXCUSED,
        "exc": AttendanceStatus.EXCUSED,
        "ex": AttendanceStatus.EXCUSED,
        "ea": AttendanceStatus.EXCUSED,
        "excused absence": AttendanceStatus.EXCUSED,
        # Unexcused variations
        "u": AttendanceStatus.UNEXCUSED,
        "unexcused": AttendanceStatus.UNEXCUSED,
        "unex": AttendanceStatus.UNEXCUSED,
        "ua": AttendanceStatus.UNEXCUSED,
        "unexcused absence": AttendanceStatus.UNEXCUSED,
        # Remote variations
        "r": AttendanceStatus.REMOTE,
        "remote": AttendanceStatus.REMOTE,
        "virtual": AttendanceStatus.REMOTE,
        "v": AttendanceStatus.REMOTE,
        "online": AttendanceStatus.REMOTE,
        # Early departure
        "ed": AttendanceStatus.EARLY_DEPARTURE,
        "early": AttendanceStatus.EARLY_DEPARTURE,
        "early departure": AttendanceStatus.EARLY_DEPARTURE,
        "left early": AttendanceStatus.EARLY_DEPARTURE,
    }

    def __init__(self):
        self.unmapped_codes: Set[str] = set()
        self.custom_mappings: Dict[str, AttendanceStatus] = {}

    def add_custom_mapping(self, code: str, status: AttendanceStatus):
        """Add a custom code mapping."""
        self.custom_mappings[code.lower().strip()] = status

    def map_code(self, code: str) -> Tuple[AttendanceStatus, bool]:
        """
        Map an attendance code to canonical status.
        Returns (status, was_mapped).
        """
        if not code:
            return AttendanceStatus.ABSENT, False

        normalized = str(code).lower().strip()

        # Check custom mappings first
        if normalized in self.custom_mappings:
            return self.custom_mappings[normalized], True

        # Check standard mappings
        if normalized in self.CODE_MAPPINGS:
            return self.CODE_MAPPINGS[normalized], True

        # Track unmapped codes
        self.unmapped_codes.add(code)
        return AttendanceStatus.ABSENT, False

    def get_unmapped_codes(self) -> List[str]:
        """Get list of codes that couldn't be mapped."""
        return list(self.unmapped_codes)


class AttendanceProcessor:
    """
    Processes and normalizes attendance data from various sources.
    """

    def __init__(self):
        self.records: Dict[str, List[AttendanceRecord]] = {}  # student_id -> records
        self.daily_summaries: Dict[str, Dict[date, DailyAttendanceSummary]] = {}
        self.aggregates: Dict[str, AttendanceAggregate] = {}
        self.issues: List[Dict[str, Any]] = []
        self.code_mapper = AttendanceCodeMapper()

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
        ]

        date_str = str(date_str).strip()
        # Remove ordinal suffixes
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def process_record(self, record: Dict[str, Any], source: str = "default") -> AttendanceRecord:
        """Process a single attendance record."""
        student_id = str(record.get("StudentID", record.get("student_id", "")))
        date_value = self.parse_date(record.get("Date", record.get("date", "")))
        raw_code = str(record.get("Status", record.get("status", ""))).strip()

        # Map the attendance code
        status, was_mapped = self.code_mapper.map_code(raw_code)
        if not was_mapped and raw_code:
            self.issues.append({
                "type": "unmapped_code",
                "student_id": student_id,
                "date": str(date_value),
                "code": raw_code,
            })

        # Determine attendance type
        period = record.get("Period", record.get("period"))
        if period is not None:
            try:
                period_int = int(period)
                attendance_type = AttendanceType.PERIOD
            except (ValueError, TypeError):
                period_int = None
                attendance_type = AttendanceType.DAILY
        else:
            period_int = None
            attendance_type = AttendanceType.DAILY

        attendance_record = AttendanceRecord(
            id=str(record.get("ID", record.get("id", f"{student_id}-{date_value}-{period_int or 0}"))),
            student_id=student_id,
            date=date_value or date.today(),
            status=status,
            attendance_type=attendance_type,
            period=period_int,
            teacher_name=str(record.get("Teacher", record.get("teacher", ""))).strip().title(),
            notes=record.get("Notes", record.get("notes")),
            source_code=raw_code,
            source_system=source
        )

        # Store record
        if student_id not in self.records:
            self.records[student_id] = []
        self.records[student_id].append(attendance_record)

        return attendance_record

    def find_duplicates(self, student_id: str) -> List[Tuple[AttendanceRecord, AttendanceRecord]]:
        """Find duplicate attendance records for a student."""
        duplicates = []
        records = self.records.get(student_id, [])

        seen: Dict[str, AttendanceRecord] = {}
        for record in records:
            key = f"{record.date}-{record.period or 'daily'}"
            if key in seen:
                duplicates.append((seen[key], record))
                self.issues.append({
                    "type": "duplicate_attendance",
                    "student_id": student_id,
                    "date": str(record.date),
                    "period": record.period,
                })
            else:
                seen[key] = record

        return duplicates

    def build_daily_summary(self, student_id: str, target_date: date) -> DailyAttendanceSummary:
        """Build daily attendance summary from period records."""
        records = self.records.get(student_id, [])
        day_records = [r for r in records if r.date == target_date]

        summary = DailyAttendanceSummary(
            student_id=student_id,
            date=target_date,
            period_records=day_records
        )
        summary.calculate_daily_status()

        # Store summary
        if student_id not in self.daily_summaries:
            self.daily_summaries[student_id] = {}
        self.daily_summaries[student_id][target_date] = summary

        return summary

    def calculate_aggregate(self, student_id: str, start: date, end: date) -> AttendanceAggregate:
        """Calculate aggregate attendance statistics for a date range."""
        records = self.records.get(student_id, [])
        relevant_records = [r for r in records if start <= r.date <= end]

        # Group by date
        by_date: Dict[date, List[AttendanceRecord]] = {}
        for record in relevant_records:
            if record.date not in by_date:
                by_date[record.date] = []
            by_date[record.date].append(record)

        aggregate = AttendanceAggregate(
            student_id=student_id,
            start_date=start,
            end_date=end,
            total_days=len(by_date)
        )

        for record_date, day_records in by_date.items():
            summary = self.build_daily_summary(student_id, record_date)
            status = summary.daily_status

            if status == AttendanceStatus.PRESENT:
                aggregate.days_present += 1
            elif status == AttendanceStatus.TARDY:
                aggregate.days_tardy += 1
            elif status == AttendanceStatus.EXCUSED:
                aggregate.days_excused += 1
            elif status == AttendanceStatus.UNEXCUSED:
                aggregate.days_unexcused += 1
            elif status in [AttendanceStatus.ABSENT, AttendanceStatus.HALF_DAY]:
                aggregate.days_absent += 1

        aggregate.calculate_rate()
        self.aggregates[student_id] = aggregate

        return aggregate

    def verify_totals(self, student_id: str, expected_present: int,
                      expected_absent: int) -> Dict[str, Any]:
        """
        Verify aggregate totals match expected values.
        Used for reconciliation with source systems.
        """
        aggregate = self.aggregates.get(student_id)
        if not aggregate:
            return {
                "verified": False,
                "error": "No aggregate data found",
            }

        actual_present = aggregate.days_present + aggregate.days_tardy
        present_match = actual_present == expected_present
        absent_match = (aggregate.days_absent + aggregate.days_excused +
                        aggregate.days_unexcused) == expected_absent

        result = {
            "verified": present_match and absent_match,
            "expected_present": expected_present,
            "actual_present": actual_present,
            "present_match": present_match,
            "expected_absent": expected_absent,
            "actual_absent": aggregate.days_absent,
            "absent_match": absent_match,
        }

        if not result["verified"]:
            self.issues.append({
                "type": "total_mismatch",
                "student_id": student_id,
                **result
            })

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get attendance processing statistics."""
        total_records = sum(len(r) for r in self.records.values())
        unmapped = self.code_mapper.get_unmapped_codes()

        return {
            "total_students": len(self.records),
            "total_records": total_records,
            "daily_summaries": sum(len(s) for s in self.daily_summaries.values()),
            "aggregates_calculated": len(self.aggregates),
            "issues_found": len(self.issues),
            "unmapped_codes": unmapped,
            "unmapped_code_count": len(unmapped),
        }
