"""
Ed-Fi Export Module
Based on DMaaS Playbook Section 1A.2

Generates JSON conforming to Ed-Fi data standard for state reporting:
- Students, StudentSchoolAssociations
- Staff, StaffEducationOrganizationAssignments
- Courses, Sections, StudentSectionAssociations
- Attendance events, Grades
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import json


@dataclass
class EdFiStudent:
    """Ed-Fi Student record."""
    studentUniqueId: str
    firstName: str
    lastSurname: str
    middleName: str = ""
    birthDate: str = ""
    electronicMails: List[Dict[str, str]] = field(default_factory=list)
    telephones: List[Dict[str, str]] = field(default_factory=list)
    addresses: List[Dict[str, Any]] = field(default_factory=list)
    identificationCodes: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "studentUniqueId": self.studentUniqueId,
            "firstName": self.firstName,
            "lastSurname": self.lastSurname,
            "birthDate": self.birthDate,
        }
        if self.middleName:
            result["middleName"] = self.middleName
        if self.electronicMails:
            result["electronicMails"] = self.electronicMails
        if self.telephones:
            result["telephones"] = self.telephones
        if self.addresses:
            result["addresses"] = self.addresses
        if self.identificationCodes:
            result["identificationCodes"] = self.identificationCodes
        return result


@dataclass
class EdFiStudentSchoolAssociation:
    """Ed-Fi Student School Association record."""
    studentReference: Dict[str, str]
    schoolReference: Dict[str, str]
    entryDate: str
    entryGradeLevelDescriptor: str
    exitWithdrawDate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "studentReference": self.studentReference,
            "schoolReference": self.schoolReference,
            "entryDate": self.entryDate,
            "entryGradeLevelDescriptor": self.entryGradeLevelDescriptor,
        }
        if self.exitWithdrawDate:
            result["exitWithdrawDate"] = self.exitWithdrawDate
        return result


@dataclass
class EdFiStaff:
    """Ed-Fi Staff record."""
    staffUniqueId: str
    firstName: str
    lastSurname: str
    middleName: str = ""
    electronicMails: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "staffUniqueId": self.staffUniqueId,
            "firstName": self.firstName,
            "lastSurname": self.lastSurname,
        }
        if self.middleName:
            result["middleName"] = self.middleName
        if self.electronicMails:
            result["electronicMails"] = self.electronicMails
        return result


@dataclass
class EdFiCourse:
    """Ed-Fi Course record."""
    courseCode: str
    courseTitle: str
    educationOrganizationReference: Dict[str, str]
    numberOfParts: int = 1
    identificationCodes: List[Dict[str, str]] = field(default_factory=list)
    levelCharacteristics: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "courseCode": self.courseCode,
            "courseTitle": self.courseTitle,
            "educationOrganizationReference": self.educationOrganizationReference,
            "numberOfParts": self.numberOfParts,
        }
        if self.identificationCodes:
            result["identificationCodes"] = self.identificationCodes
        if self.levelCharacteristics:
            result["levelCharacteristics"] = self.levelCharacteristics
        return result


@dataclass
class EdFiSection:
    """Ed-Fi Section record."""
    sectionIdentifier: str
    courseOfferingReference: Dict[str, Any]
    locationReference: Dict[str, str] = field(default_factory=dict)
    availableCredits: float = 0.0
    sequenceOfCourse: int = 1

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "sectionIdentifier": self.sectionIdentifier,
            "courseOfferingReference": self.courseOfferingReference,
            "sequenceOfCourse": self.sequenceOfCourse,
        }
        if self.availableCredits:
            result["availableCredits"] = self.availableCredits
        if self.locationReference:
            result["locationReference"] = self.locationReference
        return result


@dataclass
class EdFiStudentSectionAssociation:
    """Ed-Fi Student Section Association record."""
    studentReference: Dict[str, str]
    sectionReference: Dict[str, Any]
    beginDate: str
    endDate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "studentReference": self.studentReference,
            "sectionReference": self.sectionReference,
            "beginDate": self.beginDate,
        }
        if self.endDate:
            result["endDate"] = self.endDate
        return result


@dataclass
class EdFiGrade:
    """Ed-Fi Grade record."""
    studentSectionAssociationReference: Dict[str, Any]
    gradingPeriodReference: Dict[str, Any]
    gradeTypeDescriptor: str
    letterGradeEarned: str = ""
    numericGradeEarned: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "studentSectionAssociationReference": self.studentSectionAssociationReference,
            "gradingPeriodReference": self.gradingPeriodReference,
            "gradeTypeDescriptor": self.gradeTypeDescriptor,
        }
        if self.letterGradeEarned:
            result["letterGradeEarned"] = self.letterGradeEarned
        if self.numericGradeEarned:
            result["numericGradeEarned"] = self.numericGradeEarned
        return result


@dataclass
class EdFiStudentSchoolAttendanceEvent:
    """Ed-Fi Student School Attendance Event record."""
    studentReference: Dict[str, str]
    schoolReference: Dict[str, str]
    eventDate: str
    sessionReference: Dict[str, Any]
    attendanceEventCategoryDescriptor: str
    attendanceEventReason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "studentReference": self.studentReference,
            "schoolReference": self.schoolReference,
            "eventDate": self.eventDate,
            "sessionReference": self.sessionReference,
            "attendanceEventCategoryDescriptor": self.attendanceEventCategoryDescriptor,
        }
        if self.attendanceEventReason:
            result["attendanceEventReason"] = self.attendanceEventReason
        return result


class EdFiExporter:
    """
    Exports data to Ed-Fi JSON format.
    """

    # Ed-Fi descriptor mappings
    GRADE_LEVEL_DESCRIPTORS = {
        -1: "uri://ed-fi.org/GradeLevelDescriptor#Preschool/Prekindergarten",
        0: "uri://ed-fi.org/GradeLevelDescriptor#Kindergarten",
        1: "uri://ed-fi.org/GradeLevelDescriptor#First grade",
        2: "uri://ed-fi.org/GradeLevelDescriptor#Second grade",
        3: "uri://ed-fi.org/GradeLevelDescriptor#Third grade",
        4: "uri://ed-fi.org/GradeLevelDescriptor#Fourth grade",
        5: "uri://ed-fi.org/GradeLevelDescriptor#Fifth grade",
        6: "uri://ed-fi.org/GradeLevelDescriptor#Sixth grade",
        7: "uri://ed-fi.org/GradeLevelDescriptor#Seventh grade",
        8: "uri://ed-fi.org/GradeLevelDescriptor#Eighth grade",
        9: "uri://ed-fi.org/GradeLevelDescriptor#Ninth grade",
        10: "uri://ed-fi.org/GradeLevelDescriptor#Tenth grade",
        11: "uri://ed-fi.org/GradeLevelDescriptor#Eleventh grade",
        12: "uri://ed-fi.org/GradeLevelDescriptor#Twelfth grade",
    }

    ATTENDANCE_DESCRIPTORS = {
        "present": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#In Attendance",
        "absent": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Unexcused Absence",
        "tardy": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Tardy",
        "excused": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Excused Absence",
        "unexcused": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Unexcused Absence",
    }

    def __init__(self, school_id: str = "255901001", school_year: int = 2024):
        self.school_id = school_id
        self.school_year = school_year
        self.students: List[EdFiStudent] = []
        self.student_school_associations: List[EdFiStudentSchoolAssociation] = []
        self.staff: List[EdFiStaff] = []
        self.courses: List[EdFiCourse] = []
        self.sections: List[EdFiSection] = []
        self.student_section_associations: List[EdFiStudentSectionAssociation] = []
        self.grades: List[EdFiGrade] = []
        self.attendance_events: List[EdFiStudentSchoolAttendanceEvent] = []

    def get_grade_level_descriptor(self, grade: int) -> str:
        """Get Ed-Fi grade level descriptor."""
        return self.GRADE_LEVEL_DESCRIPTORS.get(
            grade,
            f"uri://ed-fi.org/GradeLevelDescriptor#Grade {grade}"
        )

    def get_attendance_descriptor(self, status: str) -> str:
        """Get Ed-Fi attendance descriptor."""
        return self.ATTENDANCE_DESCRIPTORS.get(
            status.lower(),
            "uri://ed-fi.org/AttendanceEventCategoryDescriptor#In Attendance"
        )

    def add_student(self, student_data: Dict[str, Any]) -> EdFiStudent:
        """Add a student record."""
        student = EdFiStudent(
            studentUniqueId=str(student_data.get("student_id", "")),
            firstName=str(student_data.get("first_name", "")).strip().title(),
            lastSurname=str(student_data.get("last_name", "")).strip().title(),
            middleName=str(student_data.get("middle_name", "")).strip().title() if student_data.get("middle_name") else "",
            birthDate=str(student_data.get("date_of_birth", "")) if student_data.get("date_of_birth") else "",
        )

        # Add email
        if student_data.get("email"):
            student.electronicMails.append({
                "electronicMailAddress": student_data["email"],
                "electronicMailTypeDescriptor": "uri://ed-fi.org/ElectronicMailTypeDescriptor#Home/Personal"
            })

        # Add phone
        if student_data.get("phone"):
            student.telephones.append({
                "telephoneNumber": student_data["phone"],
                "telephoneNumberTypeDescriptor": "uri://ed-fi.org/TelephoneNumberTypeDescriptor#Home"
            })

        # Add identification codes
        if student_data.get("state_id"):
            student.identificationCodes.append({
                "identificationCode": student_data["state_id"],
                "studentIdentificationSystemDescriptor": "uri://ed-fi.org/StudentIdentificationSystemDescriptor#State"
            })

        self.students.append(student)

        # Create student-school association
        grade = student_data.get("grade", 9)
        try:
            grade_int = int(grade)
        except (ValueError, TypeError):
            grade_int = 9

        enrollment_date = student_data.get("enrollment_date", str(date.today()))

        association = EdFiStudentSchoolAssociation(
            studentReference={"studentUniqueId": student.studentUniqueId},
            schoolReference={"schoolId": self.school_id},
            entryDate=str(enrollment_date),
            entryGradeLevelDescriptor=self.get_grade_level_descriptor(grade_int)
        )
        self.student_school_associations.append(association)

        return student

    def add_staff(self, staff_data: Dict[str, Any]) -> EdFiStaff:
        """Add a staff record."""
        name = str(staff_data.get("name", "")).strip()
        name_parts = name.split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        staff = EdFiStaff(
            staffUniqueId=str(staff_data.get("id", first_name.lower())),
            firstName=first_name.title(),
            lastSurname=last_name.title(),
        )

        if staff_data.get("email"):
            staff.electronicMails.append({
                "electronicMailAddress": staff_data["email"],
                "electronicMailTypeDescriptor": "uri://ed-fi.org/ElectronicMailTypeDescriptor#Work"
            })

        self.staff.append(staff)
        return staff

    def add_course(self, course_data: Dict[str, Any]) -> EdFiCourse:
        """Add a course record."""
        course = EdFiCourse(
            courseCode=str(course_data.get("code", "")),
            courseTitle=str(course_data.get("name", "")).strip().title(),
            educationOrganizationReference={"educationOrganizationId": self.school_id},
        )

        if course_data.get("is_honors") or course_data.get("is_ap"):
            level = "Honors" if course_data.get("is_honors") else "Advanced Placement"
            course.levelCharacteristics.append({
                "courseLevelCharacteristicDescriptor": f"uri://ed-fi.org/CourseLevelCharacteristicDescriptor#{level}"
            })

        self.courses.append(course)
        return course

    def add_grade(self, grade_data: Dict[str, Any]) -> EdFiGrade:
        """Add a grade record."""
        grade = EdFiGrade(
            studentSectionAssociationReference={
                "studentUniqueId": str(grade_data.get("student_id", "")),
                "sectionIdentifier": str(grade_data.get("course_code", "")),
                "localCourseCode": str(grade_data.get("course_code", "")),
                "schoolId": self.school_id,
                "schoolYear": self.school_year,
                "sessionName": grade_data.get("term", "Fall"),
            },
            gradingPeriodReference={
                "gradingPeriodDescriptor": "uri://ed-fi.org/GradingPeriodDescriptor#End of Year",
                "periodSequence": 1,
                "schoolId": self.school_id,
                "schoolYear": self.school_year,
            },
            gradeTypeDescriptor="uri://ed-fi.org/GradeTypeDescriptor#Semester",
            letterGradeEarned=str(grade_data.get("letter_grade", "")),
            numericGradeEarned=float(grade_data.get("numeric_grade", 0)) if grade_data.get("numeric_grade") else 0,
        )
        self.grades.append(grade)
        return grade

    def add_attendance_event(self, attendance_data: Dict[str, Any]) -> EdFiStudentSchoolAttendanceEvent:
        """Add an attendance event record."""
        status = str(attendance_data.get("status", "present")).lower()

        event = EdFiStudentSchoolAttendanceEvent(
            studentReference={"studentUniqueId": str(attendance_data.get("student_id", ""))},
            schoolReference={"schoolId": self.school_id},
            eventDate=str(attendance_data.get("date", "")),
            sessionReference={
                "schoolId": self.school_id,
                "schoolYear": self.school_year,
                "sessionName": "2023-2024",
            },
            attendanceEventCategoryDescriptor=self.get_attendance_descriptor(status),
            attendanceEventReason=str(attendance_data.get("notes", "")),
        )
        self.attendance_events.append(event)
        return event

    def export_students_json(self) -> str:
        """Export students to JSON."""
        return json.dumps([s.to_dict() for s in self.students], indent=2)

    def export_student_school_associations_json(self) -> str:
        """Export student-school associations to JSON."""
        return json.dumps([a.to_dict() for a in self.student_school_associations], indent=2)

    def export_staff_json(self) -> str:
        """Export staff to JSON."""
        return json.dumps([s.to_dict() for s in self.staff], indent=2)

    def export_courses_json(self) -> str:
        """Export courses to JSON."""
        return json.dumps([c.to_dict() for c in self.courses], indent=2)

    def export_grades_json(self) -> str:
        """Export grades to JSON."""
        return json.dumps([g.to_dict() for g in self.grades], indent=2)

    def export_attendance_json(self) -> str:
        """Export attendance events to JSON."""
        return json.dumps([a.to_dict() for a in self.attendance_events], indent=2)

    def export_all(self) -> Dict[str, str]:
        """Export all Ed-Fi files."""
        return {
            "students.json": self.export_students_json(),
            "studentSchoolAssociations.json": self.export_student_school_associations_json(),
            "staff.json": self.export_staff_json(),
            "courses.json": self.export_courses_json(),
            "grades.json": self.export_grades_json(),
            "studentSchoolAttendanceEvents.json": self.export_attendance_json(),
        }

    def export_combined_json(self) -> str:
        """Export all data as a single combined JSON."""
        return json.dumps({
            "students": [s.to_dict() for s in self.students],
            "studentSchoolAssociations": [a.to_dict() for a in self.student_school_associations],
            "staff": [s.to_dict() for s in self.staff],
            "courses": [c.to_dict() for c in self.courses],
            "grades": [g.to_dict() for g in self.grades],
            "studentSchoolAttendanceEvents": [a.to_dict() for a in self.attendance_events],
        }, indent=2)

    def get_stats(self) -> Dict[str, int]:
        """Get export statistics."""
        return {
            "students": len(self.students),
            "student_school_associations": len(self.student_school_associations),
            "staff": len(self.staff),
            "courses": len(self.courses),
            "sections": len(self.sections),
            "student_section_associations": len(self.student_section_associations),
            "grades": len(self.grades),
            "attendance_events": len(self.attendance_events),
        }
