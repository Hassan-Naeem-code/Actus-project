"""
Canonical Data Model for School Data Migration
Based on DMaaS Playbook Section 4B

This module defines the canonical entities used for data migration:
- Person (natural person with identifiers)
- PersonRole (Student/Guardian/Staff - time-bounded)
- Household (grouping construct)
- Relationship (Person<->Person, custody constraints)
- Enrollment (student<->school with start/end)
- Course, Section, RosterMembership
- AttendanceEvent (daily/period with codes)
- TranscriptCourse (grades, credits, GPA)
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import hashlib
import json


class RoleType(Enum):
    """Types of roles a person can have in the education system."""
    STUDENT = "student"
    GUARDIAN = "guardian"
    STAFF = "staff"
    TEACHER = "teacher"
    ADMINISTRATOR = "administrator"


class RelationshipType(Enum):
    """Types of relationships between persons."""
    PARENT = "parent"
    GUARDIAN = "guardian"
    FATHER = "father"
    MOTHER = "mother"
    STEPPARENT = "stepparent"
    GRANDPARENT = "grandparent"
    SIBLING = "sibling"
    OTHER_FAMILY = "other_family"
    EMERGENCY_CONTACT = "emergency_contact"


class CustodyType(Enum):
    """Types of custody arrangements."""
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    JOINT = "joint"
    PRIMARY = "primary"
    SECONDARY = "secondary"


class EnrollmentStatus(Enum):
    """Status of student enrollment."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    PENDING = "pending"


class AttendanceStatus(Enum):
    """Canonical attendance status codes."""
    PRESENT = "present"
    ABSENT = "absent"
    TARDY = "tardy"
    EXCUSED_ABSENT = "excused_absent"
    UNEXCUSED_ABSENT = "unexcused_absent"
    EARLY_DEPARTURE = "early_departure"
    REMOTE = "remote"


class GradeScale(Enum):
    """Grade scale types."""
    LETTER = "letter"
    NUMERIC = "numeric"
    PERCENTAGE = "percentage"
    PASS_FAIL = "pass_fail"
    STANDARDS_BASED = "standards_based"


class AttendanceCode(Enum):
    """Standard attendance codes mapping."""
    P = "present"
    A = "absent"
    T = "tardy"
    E = "excused"
    U = "unexcused"
    R = "remote"


@dataclass
class Person:
    """
    A natural person with identifiers.
    This is the core entity representing any individual in the system.
    """
    id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    # Multiple identifiers (golden identifier strategy)
    state_id: Optional[str] = None
    local_id: Optional[str] = None
    source_ids: Dict[str, str] = field(default_factory=dict)  # source_system -> id

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_system: Optional[str] = None

    def full_name(self) -> str:
        """Return the full name of the person."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    def generate_hash(self) -> str:
        """Generate a hash for data integrity verification."""
        data = f"{self.id}|{self.first_name}|{self.last_name}|{self.date_of_birth}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "date_of_birth": str(self.date_of_birth) if self.date_of_birth else None,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "state_id": self.state_id,
            "local_id": self.local_id,
            "source_ids": self.source_ids,
            "source_system": self.source_system,
        }


@dataclass
class PersonRole:
    """
    A time-bounded role for a person (Student, Guardian, Staff).
    A person can have multiple roles with different time periods.
    """
    id: str
    person_id: str
    role_type: RoleType
    organization_id: str
    start_date: date
    end_date: Optional[date] = None
    is_primary: bool = True
    grade_level: Optional[int] = None  # For students
    title: Optional[str] = None  # For staff

    def is_active(self, as_of: date = None) -> bool:
        """Check if the role is active as of a given date."""
        check_date = as_of or date.today()
        if self.end_date:
            return self.start_date <= check_date <= self.end_date
        return self.start_date <= check_date


@dataclass
class Household:
    """
    A grouping construct for persons living together.
    Used for linking students to guardians and managing contact information.
    """
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    member_ids: List[str] = field(default_factory=list)
    is_primary: bool = True

    def add_member(self, person_id: str):
        """Add a member to the household."""
        if person_id not in self.member_ids:
            self.member_ids.append(person_id)


@dataclass
class Relationship:
    """
    A relationship between two persons with custody constraints.
    """
    id: str
    person_id: str  # The guardian/parent
    related_person_id: str  # The student
    relationship_type: RelationshipType
    custody_type: CustodyType = CustodyType.FULL
    is_emergency_contact: bool = False
    emergency_priority: int = 0  # 1 = primary, 2 = secondary, etc.
    can_pickup: bool = True
    receives_mail: bool = True
    receives_grades: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "person_id": self.person_id,
            "related_person_id": self.related_person_id,
            "relationship_type": self.relationship_type.value,
            "custody_type": self.custody_type.value,
            "is_emergency_contact": self.is_emergency_contact,
            "emergency_priority": self.emergency_priority,
        }


@dataclass
class Enrollment:
    """
    Student enrollment at a school with start/end dates.
    """
    id: str
    student_id: str
    school_id: str
    school_name: str
    grade_level: int
    start_date: date
    end_date: Optional[date] = None
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    is_primary: bool = True

    def is_active(self, as_of: date = None) -> bool:
        """Check if enrollment is active as of a given date."""
        check_date = as_of or date.today()
        if self.end_date:
            return self.start_date <= check_date <= self.end_date
        return self.start_date <= check_date and self.status == EnrollmentStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "school_id": self.school_id,
            "school_name": self.school_name,
            "grade_level": self.grade_level,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date) if self.end_date else None,
            "status": self.status.value,
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
        }


@dataclass
class Course:
    """
    A course in the course catalog.
    """
    id: str
    code: str
    name: str
    description: Optional[str] = None
    credits: float = 0.0
    grade_levels: List[int] = field(default_factory=list)
    subject_area: Optional[str] = None
    is_honors: bool = False
    is_ap: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "credits": self.credits,
            "subject_area": self.subject_area,
            "is_honors": self.is_honors,
            "is_ap": self.is_ap,
        }


@dataclass
class Section:
    """
    A section (class instance) of a course.
    """
    id: str
    course_id: str
    section_code: str
    term: str
    school_year: str
    instructor_id: Optional[str] = None
    instructor_name: Optional[str] = None
    room: Optional[str] = None
    period: Optional[str] = None
    max_enrollment: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "section_code": self.section_code,
            "term": self.term,
            "school_year": self.school_year,
            "instructor_id": self.instructor_id,
            "instructor_name": self.instructor_name,
        }


@dataclass
class RosterMembership:
    """
    A student's membership in a class section.
    """
    id: str
    student_id: str
    section_id: str
    start_date: date
    end_date: Optional[date] = None
    is_primary: bool = True

    def is_active(self, as_of: date = None) -> bool:
        """Check if membership is active as of a given date."""
        check_date = as_of or date.today()
        if self.end_date:
            return self.start_date <= check_date <= self.end_date
        return self.start_date <= check_date


@dataclass
class AttendanceEvent:
    """
    An attendance event (daily or period-based).
    """
    id: str
    student_id: str
    date: date
    status: AttendanceStatus
    period: Optional[int] = None  # None for daily attendance
    section_id: Optional[str] = None
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    notes: Optional[str] = None
    source_code: Optional[str] = None  # Original code from source system

    def is_present(self) -> bool:
        """Check if the attendance status indicates presence."""
        return self.status in [AttendanceStatus.PRESENT, AttendanceStatus.TARDY, AttendanceStatus.REMOTE]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "date": str(self.date),
            "status": self.status.value,
            "period": self.period,
            "section_id": self.section_id,
            "teacher_name": self.teacher_name,
            "notes": self.notes,
        }


@dataclass
class TranscriptCourse:
    """
    A course on a student's transcript (historical grades).
    """
    id: str
    student_id: str
    course_id: str
    course_code: str
    course_name: str
    term: str
    school_year: str
    letter_grade: Optional[str] = None
    numeric_grade: Optional[float] = None
    credits_attempted: float = 0.0
    credits_earned: float = 0.0
    grade_points: float = 0.0
    is_weighted: bool = False
    instructor_name: Optional[str] = None

    # Grade scale mapping
    LETTER_TO_POINTS = {
        "A+": 4.0, "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "D-": 0.7,
        "F": 0.0, "I": 0.0, "W": 0.0,
    }

    def calculate_grade_points(self) -> float:
        """Calculate grade points from letter grade."""
        if self.letter_grade:
            base_grade = self.letter_grade.upper().strip()
            points = self.LETTER_TO_POINTS.get(base_grade, 0.0)
            if self.is_weighted:
                points += 0.5  # Weight boost for honors/AP
            return points * self.credits_attempted
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "term": self.term,
            "school_year": self.school_year,
            "letter_grade": self.letter_grade,
            "numeric_grade": self.numeric_grade,
            "credits_attempted": self.credits_attempted,
            "credits_earned": self.credits_earned,
            "instructor_name": self.instructor_name,
        }
