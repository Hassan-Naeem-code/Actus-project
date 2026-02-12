"""
Grades & Transcript Processing Module
Based on DMaaS Playbook Section 1.1.4

Provides:
- Grade Scale Translation: A/B/C -> numeric, handle variations
- Transcript vs Gradebook: Separate historical from in-progress
- GPA Calculation: Weighted/unweighted, handle edge cases
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re


class GradeType(Enum):
    """Types of grades."""
    LETTER = "letter"
    NUMERIC = "numeric"
    PERCENTAGE = "percentage"
    PASS_FAIL = "pass_fail"
    STANDARDS_BASED = "standards_based"


class GradeStatus(Enum):
    """Status of a grade."""
    FINAL = "final"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"
    WITHDRAWN = "withdrawn"
    TRANSFER = "transfer"


@dataclass
class GradeRecord:
    """A single grade record."""
    id: str
    student_id: str
    course_code: str
    course_name: str
    term: str
    school_year: str
    raw_grade: str
    letter_grade: Optional[str] = None
    numeric_grade: Optional[float] = None
    credits_attempted: float = 0.0
    credits_earned: float = 0.0
    grade_points: float = 0.0
    is_weighted: bool = False
    is_honors: bool = False
    is_ap: bool = False
    instructor_name: Optional[str] = None
    status: GradeStatus = GradeStatus.FINAL
    source_system: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "term": self.term,
            "school_year": self.school_year,
            "raw_grade": self.raw_grade,
            "letter_grade": self.letter_grade,
            "numeric_grade": self.numeric_grade,
            "credits_attempted": self.credits_attempted,
            "credits_earned": self.credits_earned,
            "grade_points": self.grade_points,
            "is_weighted": self.is_weighted,
            "instructor_name": self.instructor_name,
            "status": self.status.value,
        }


@dataclass
class TranscriptEntry:
    """A transcript entry combining course and grade information."""
    course_code: str
    course_name: str
    term: str
    school_year: str
    letter_grade: str
    credits_attempted: float
    credits_earned: float
    grade_points: float
    is_weighted: bool = False

    def quality_points(self) -> float:
        """Calculate quality points for GPA."""
        return self.grade_points * self.credits_attempted


@dataclass
class StudentTranscript:
    """A student's complete transcript."""
    student_id: str
    entries: List[TranscriptEntry] = field(default_factory=list)
    cumulative_gpa: float = 0.0
    weighted_gpa: float = 0.0
    total_credits_attempted: float = 0.0
    total_credits_earned: float = 0.0

    def calculate_gpa(self) -> Tuple[float, float]:
        """Calculate cumulative and weighted GPA."""
        if not self.entries:
            return 0.0, 0.0

        total_quality_points = 0.0
        weighted_quality_points = 0.0
        total_credits = 0.0

        for entry in self.entries:
            if entry.credits_attempted > 0:
                total_quality_points += entry.grade_points * entry.credits_attempted
                # Add weight bonus for honors/AP
                weight_bonus = 0.5 if entry.is_weighted else 0.0
                weighted_quality_points += (entry.grade_points + weight_bonus) * entry.credits_attempted
                total_credits += entry.credits_attempted

        self.total_credits_attempted = total_credits
        self.cumulative_gpa = round(total_quality_points / total_credits, 3) if total_credits > 0 else 0.0
        self.weighted_gpa = round(weighted_quality_points / total_credits, 3) if total_credits > 0 else 0.0

        return self.cumulative_gpa, self.weighted_gpa

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "cumulative_gpa": self.cumulative_gpa,
            "weighted_gpa": self.weighted_gpa,
            "total_credits_attempted": self.total_credits_attempted,
            "total_credits_earned": self.total_credits_earned,
            "entry_count": len(self.entries),
        }


class GradeProcessor:
    """
    Processes and normalizes grade data from various sources.
    """

    # Standard letter grade to grade point conversion
    LETTER_TO_POINTS = {
        "A+": 4.0, "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "D-": 0.7,
        "F": 0.0,
        "P": None,  # Pass - no GPA impact
        "NP": None,  # No Pass - no GPA impact
        "I": None,  # Incomplete
        "W": None,  # Withdrawn
    }

    # Percentage to letter grade conversion
    PERCENTAGE_TO_LETTER = [
        (97, "A+"), (93, "A"), (90, "A-"),
        (87, "B+"), (83, "B"), (80, "B-"),
        (77, "C+"), (73, "C"), (70, "C-"),
        (67, "D+"), (63, "D"), (60, "D-"),
        (0, "F"),
    ]

    # Numeric (4.0 scale) to letter grade
    NUMERIC_TO_LETTER = [
        (4.0, "A"), (3.7, "A-"),
        (3.3, "B+"), (3.0, "B"), (2.7, "B-"),
        (2.3, "C+"), (2.0, "C"), (1.7, "C-"),
        (1.3, "D+"), (1.0, "D"), (0.7, "D-"),
        (0.0, "F"),
    ]

    def __init__(self):
        self.grades: Dict[str, List[GradeRecord]] = {}  # student_id -> grades
        self.issues: List[Dict[str, Any]] = []
        self.transcripts: Dict[str, StudentTranscript] = {}

    def detect_grade_type(self, grade: str) -> GradeType:
        """Detect the type of grade value."""
        if not grade or str(grade).upper() in ["NULL", "N/A", ""]:
            return GradeType.LETTER

        grade_str = str(grade).strip().upper()

        # Check for letter grade
        if re.match(r'^[A-F][+-]?$', grade_str):
            return GradeType.LETTER

        # Check for pass/fail
        if grade_str in ["P", "NP", "PASS", "FAIL", "S", "U"]:
            return GradeType.PASS_FAIL

        # Check for percentage
        try:
            value = float(grade_str.replace("%", ""))
            if 0 <= value <= 100:
                return GradeType.PERCENTAGE
            elif 0 <= value <= 5:
                return GradeType.NUMERIC
        except ValueError:
            pass

        return GradeType.LETTER

    def normalize_letter_grade(self, grade: str) -> Optional[str]:
        """Normalize letter grade to standard form."""
        if not grade or str(grade).upper() in ["NULL", "N/A", ""]:
            return None

        grade_str = str(grade).strip().upper()

        # Handle common variations
        variations = {
            "A PLUS": "A+", "A MINUS": "A-",
            "B PLUS": "B+", "B MINUS": "B-",
            "C PLUS": "C+", "C MINUS": "C-",
            "D PLUS": "D+", "D MINUS": "D-",
            "PASS": "P", "FAIL": "F",
            "SATISFACTORY": "P", "UNSATISFACTORY": "F",
            "S": "P", "U": "F",
        }

        if grade_str in variations:
            return variations[grade_str]

        # Standard letter grades
        if re.match(r'^[A-F][+-]?$', grade_str):
            return grade_str

        return None

    def percentage_to_letter(self, percentage: float) -> str:
        """Convert percentage to letter grade."""
        for threshold, letter in self.PERCENTAGE_TO_LETTER:
            if percentage >= threshold:
                return letter
        return "F"

    def numeric_to_letter(self, numeric: float) -> str:
        """Convert numeric (4.0 scale) grade to letter grade."""
        for threshold, letter in self.NUMERIC_TO_LETTER:
            if numeric >= threshold:
                return letter
        return "F"

    def letter_to_points(self, letter: str) -> Optional[float]:
        """Convert letter grade to grade points."""
        if not letter:
            return None
        normalized = self.normalize_letter_grade(letter)
        if normalized:
            return self.LETTER_TO_POINTS.get(normalized)
        return None

    def process_grade(self, record: Dict[str, Any], source: str = "default") -> GradeRecord:
        """Process a single grade record from source data."""
        student_id = str(record.get("STUDENT_ID", record.get("student_id", "")))
        raw_grade = str(record.get("GRADE", record.get("grade", ""))).strip()

        # Detect and convert grade
        grade_type = self.detect_grade_type(raw_grade)

        if grade_type == GradeType.PERCENTAGE:
            try:
                percentage = float(raw_grade.replace("%", ""))
                letter_grade = self.percentage_to_letter(percentage)
                numeric_grade = percentage
            except ValueError:
                letter_grade = None
                numeric_grade = None
        elif grade_type == GradeType.NUMERIC:
            try:
                numeric = float(raw_grade)
                letter_grade = self.numeric_to_letter(numeric)
                numeric_grade = numeric
            except ValueError:
                letter_grade = None
                numeric_grade = None
        else:
            letter_grade = self.normalize_letter_grade(raw_grade)
            numeric_grade = self.letter_to_points(letter_grade) if letter_grade else None

        # Get grade points
        grade_points = self.letter_to_points(letter_grade) if letter_grade else 0.0

        # Parse credits
        try:
            credits = float(record.get("CREDITS", record.get("credits", 0)))
        except (ValueError, TypeError):
            credits = 0.0

        # Determine if weighted (honors/AP)
        course_name = str(record.get("COURSE_NAME", record.get("course_name", ""))).upper()
        is_honors = "HONORS" in course_name or "HON" in course_name
        is_ap = "AP " in course_name or course_name.startswith("AP")

        # Normalize term
        term = str(record.get("SEMESTER", record.get("term", ""))).strip().title()

        # Create grade record
        grade_record = GradeRecord(
            id=f"{student_id}-{record.get('COURSE_CODE', 'UNKNOWN')}-{term}",
            student_id=student_id,
            course_code=str(record.get("COURSE_CODE", record.get("course_code", ""))).upper(),
            course_name=str(record.get("COURSE_NAME", record.get("course_name", ""))).strip().title(),
            term=term,
            school_year=str(record.get("YEAR", record.get("year", ""))),
            raw_grade=raw_grade,
            letter_grade=letter_grade,
            numeric_grade=numeric_grade,
            credits_attempted=credits,
            credits_earned=credits if letter_grade and letter_grade not in ["F", "I", "W"] else 0.0,
            grade_points=grade_points or 0.0,
            is_weighted=is_honors or is_ap,
            is_honors=is_honors,
            is_ap=is_ap,
            instructor_name=str(record.get("INSTRUCTOR", record.get("instructor", ""))).strip().title(),
            source_system=source
        )

        # Track issues
        if not letter_grade and raw_grade:
            self.issues.append({
                "type": "invalid_grade",
                "student_id": student_id,
                "course_code": grade_record.course_code,
                "raw_grade": raw_grade,
            })

        # Store grade
        if student_id not in self.grades:
            self.grades[student_id] = []
        self.grades[student_id].append(grade_record)

        return grade_record

    def find_duplicates(self, student_id: str) -> List[Tuple[GradeRecord, GradeRecord]]:
        """Find duplicate grade records for a student."""
        duplicates = []
        grades = self.grades.get(student_id, [])

        for i, g1 in enumerate(grades):
            for g2 in grades[i + 1:]:
                if (g1.course_code == g2.course_code and
                        g1.term == g2.term and
                        g1.school_year == g2.school_year):
                    duplicates.append((g1, g2))
                    self.issues.append({
                        "type": "duplicate_grade",
                        "student_id": student_id,
                        "course_code": g1.course_code,
                        "term": g1.term,
                    })

        return duplicates


class TranscriptBuilder:
    """
    Builds official transcripts from grade data.
    """

    def __init__(self, grade_processor: GradeProcessor):
        self.processor = grade_processor

    def build_transcript(self, student_id: str) -> StudentTranscript:
        """Build a complete transcript for a student."""
        transcript = StudentTranscript(student_id=student_id)
        grades = self.processor.grades.get(student_id, [])

        # Remove duplicates - keep highest grade
        unique_grades: Dict[str, GradeRecord] = {}
        for grade in grades:
            key = f"{grade.course_code}-{grade.term}-{grade.school_year}"
            if key not in unique_grades:
                unique_grades[key] = grade
            elif grade.grade_points > unique_grades[key].grade_points:
                unique_grades[key] = grade

        # Create transcript entries
        for grade in unique_grades.values():
            if grade.status == GradeStatus.FINAL and grade.letter_grade:
                entry = TranscriptEntry(
                    course_code=grade.course_code,
                    course_name=grade.course_name,
                    term=grade.term,
                    school_year=grade.school_year,
                    letter_grade=grade.letter_grade,
                    credits_attempted=grade.credits_attempted,
                    credits_earned=grade.credits_earned,
                    grade_points=grade.grade_points,
                    is_weighted=grade.is_weighted
                )
                transcript.entries.append(entry)
                transcript.total_credits_earned += entry.credits_earned

        # Calculate GPA
        transcript.calculate_gpa()
        self.processor.transcripts[student_id] = transcript

        return transcript

    def get_gpa_summary(self, student_id: str) -> Dict[str, Any]:
        """Get GPA summary for a student."""
        transcript = self.processor.transcripts.get(student_id)
        if not transcript:
            transcript = self.build_transcript(student_id)

        return {
            "student_id": student_id,
            "cumulative_gpa": transcript.cumulative_gpa,
            "weighted_gpa": transcript.weighted_gpa,
            "total_credits": transcript.total_credits_attempted,
            "credits_earned": transcript.total_credits_earned,
            "course_count": len(transcript.entries),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get grade processing statistics."""
        total_grades = sum(len(g) for g in self.processor.grades.values())
        return {
            "total_students": len(self.processor.grades),
            "total_grades": total_grades,
            "transcripts_built": len(self.processor.transcripts),
            "issues_found": len(self.processor.issues),
            "invalid_grades": sum(1 for i in self.processor.issues if i["type"] == "invalid_grade"),
            "duplicate_grades": sum(1 for i in self.processor.issues if i["type"] == "duplicate_grade"),
        }
