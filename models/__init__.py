"""
EduSync AI - Canonical Data Models
Based on DMaaS Playbook Section 4B
"""

from .canonical import (
    Person,
    PersonRole,
    Household,
    Relationship,
    Enrollment,
    Course,
    Section,
    RosterMembership,
    AttendanceEvent,
    TranscriptCourse,
    GradeScale,
    AttendanceCode,
)
from .validators import DataValidator, ValidationResult

__all__ = [
    "Person",
    "PersonRole",
    "Household",
    "Relationship",
    "Enrollment",
    "Course",
    "Section",
    "RosterMembership",
    "AttendanceEvent",
    "TranscriptCourse",
    "GradeScale",
    "AttendanceCode",
    "DataValidator",
    "ValidationResult",
]
