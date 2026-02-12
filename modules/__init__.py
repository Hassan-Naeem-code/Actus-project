"""
EduSync AI - Domain Processing Modules
Based on DMaaS Playbook Sections 1.1.1-1.1.5
"""

from .identity import IdentityResolver, GoldenRecord, MatchResult
from .enrollment import EnrollmentProcessor, CalendarNormalizer
from .grades import GradeProcessor, TranscriptBuilder
from .attendance import AttendanceProcessor, AttendanceCodeMapper

__all__ = [
    "IdentityResolver",
    "GoldenRecord",
    "MatchResult",
    "EnrollmentProcessor",
    "CalendarNormalizer",
    "GradeProcessor",
    "TranscriptBuilder",
    "AttendanceProcessor",
    "AttendanceCodeMapper",
]
