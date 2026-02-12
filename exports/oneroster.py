"""
OneRoster Export Module
Based on DMaaS Playbook Section 1A.1

Generates CSV files per OneRoster 1.2 spec:
- users.csv - Students, teachers, guardians
- orgs.csv - Schools/districts
- courses.csv - Course catalog
- classes.csv - Sections
- enrollments.csv - Roster memberships
- academicSessions.csv - Terms/years
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import csv
import io
import json


@dataclass
class OneRosterUser:
    """OneRoster User record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    enabledUser: str = "true"
    role: str = "student"  # student, teacher, guardian, administrator
    username: str = ""
    givenName: str = ""
    familyName: str = ""
    middleName: str = ""
    email: str = ""
    phone: str = ""
    grades: str = ""  # Comma-separated grade levels
    orgSourcedIds: str = ""  # Comma-separated org IDs
    identifier: str = ""  # State ID or other identifier

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "enabledUser": self.enabledUser,
            "role": self.role,
            "username": self.username,
            "givenName": self.givenName,
            "familyName": self.familyName,
            "middleName": self.middleName,
            "email": self.email,
            "phone": self.phone,
            "grades": self.grades,
            "orgSourcedIds": self.orgSourcedIds,
            "identifier": self.identifier,
        }


@dataclass
class OneRosterOrg:
    """OneRoster Organization record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    name: str = ""
    type: str = "school"  # district, school
    identifier: str = ""
    parentSourcedId: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "name": self.name,
            "type": self.type,
            "identifier": self.identifier,
            "parentSourcedId": self.parentSourcedId,
        }


@dataclass
class OneRosterCourse:
    """OneRoster Course record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    title: str = ""
    courseCode: str = ""
    grades: str = ""
    orgSourcedId: str = ""
    subjectCodes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "title": self.title,
            "courseCode": self.courseCode,
            "grades": self.grades,
            "orgSourcedId": self.orgSourcedId,
            "subjectCodes": self.subjectCodes,
        }


@dataclass
class OneRosterClass:
    """OneRoster Class (Section) record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    title: str = ""
    classCode: str = ""
    classType: str = "scheduled"  # scheduled, homeroom
    courseSourcedId: str = ""
    schoolSourcedId: str = ""
    termSourcedIds: str = ""
    grades: str = ""
    periods: str = ""
    location: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "title": self.title,
            "classCode": self.classCode,
            "classType": self.classType,
            "courseSourcedId": self.courseSourcedId,
            "schoolSourcedId": self.schoolSourcedId,
            "termSourcedIds": self.termSourcedIds,
            "grades": self.grades,
            "periods": self.periods,
            "location": self.location,
        }


@dataclass
class OneRosterEnrollment:
    """OneRoster Enrollment record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    classSourcedId: str = ""
    schoolSourcedId: str = ""
    userSourcedId: str = ""
    role: str = "student"  # student, teacher
    primary: str = "true"
    beginDate: str = ""
    endDate: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "classSourcedId": self.classSourcedId,
            "schoolSourcedId": self.schoolSourcedId,
            "userSourcedId": self.userSourcedId,
            "role": self.role,
            "primary": self.primary,
            "beginDate": self.beginDate,
            "endDate": self.endDate,
        }


@dataclass
class OneRosterAcademicSession:
    """OneRoster Academic Session record."""
    sourcedId: str
    status: str = "active"
    dateLastModified: str = ""
    title: str = ""
    type: str = "term"  # schoolYear, term, gradingPeriod, semester
    startDate: str = ""
    endDate: str = ""
    parentSourcedId: str = ""
    schoolYear: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "sourcedId": self.sourcedId,
            "status": self.status,
            "dateLastModified": self.dateLastModified or datetime.now().isoformat(),
            "title": self.title,
            "type": self.type,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "parentSourcedId": self.parentSourcedId,
            "schoolYear": self.schoolYear,
        }


class OneRosterExporter:
    """
    Exports data to OneRoster 1.2 CSV format.
    """

    def __init__(self):
        self.users: List[OneRosterUser] = []
        self.orgs: List[OneRosterOrg] = []
        self.courses: List[OneRosterCourse] = []
        self.classes: List[OneRosterClass] = []
        self.enrollments: List[OneRosterEnrollment] = []
        self.academic_sessions: List[OneRosterAcademicSession] = []

    def add_student(self, student_data: Dict[str, Any], org_id: str = "SCH001") -> OneRosterUser:
        """Add a student to the export."""
        user = OneRosterUser(
            sourcedId=f"STU-{student_data.get('student_id', '')}",
            role="student",
            username=student_data.get("email", "").split("@")[0] if student_data.get("email") else "",
            givenName=str(student_data.get("first_name", "")).strip().title(),
            familyName=str(student_data.get("last_name", "")).strip().title(),
            email=student_data.get("email", ""),
            phone=student_data.get("phone", ""),
            grades=str(student_data.get("grade", "")),
            orgSourcedIds=org_id,
            identifier=str(student_data.get("student_id", "")),
            status="active" if str(student_data.get("status", "")).lower() == "active" else "tobedeleted"
        )
        self.users.append(user)
        return user

    def add_guardian(self, guardian_data: Dict[str, Any], org_id: str = "SCH001") -> OneRosterUser:
        """Add a guardian to the export."""
        user = OneRosterUser(
            sourcedId=f"GRD-{guardian_data.get('guardian_id', '')}",
            role="guardian",
            givenName=str(guardian_data.get("first_name", "")).strip().title(),
            familyName=str(guardian_data.get("last_name", "")).strip().title(),
            email=guardian_data.get("email", ""),
            phone=guardian_data.get("phone", ""),
            orgSourcedIds=org_id
        )
        self.users.append(user)
        return user

    def add_teacher(self, teacher_data: Dict[str, Any], org_id: str = "SCH001") -> OneRosterUser:
        """Add a teacher to the export."""
        name_parts = str(teacher_data.get("name", "")).strip().split(" ")
        given_name = name_parts[0] if name_parts else ""
        family_name = name_parts[-1] if len(name_parts) > 1 else ""

        user = OneRosterUser(
            sourcedId=f"TCH-{teacher_data.get('id', given_name)}",
            role="teacher",
            givenName=given_name.title(),
            familyName=family_name.title(),
            orgSourcedIds=org_id
        )
        self.users.append(user)
        return user

    def add_organization(self, org_data: Dict[str, Any]) -> OneRosterOrg:
        """Add an organization (school/district) to the export."""
        org = OneRosterOrg(
            sourcedId=str(org_data.get("id", "SCH001")),
            name=org_data.get("name", "Default School"),
            type=org_data.get("type", "school"),
            identifier=org_data.get("identifier", ""),
            parentSourcedId=org_data.get("parent_id", "")
        )
        self.orgs.append(org)
        return org

    def add_course(self, course_data: Dict[str, Any], org_id: str = "SCH001") -> OneRosterCourse:
        """Add a course to the export."""
        course = OneRosterCourse(
            sourcedId=f"CRS-{course_data.get('code', '')}",
            title=course_data.get("name", ""),
            courseCode=course_data.get("code", ""),
            orgSourcedId=org_id,
            subjectCodes=course_data.get("subject", "")
        )
        self.courses.append(course)
        return course

    def add_class(self, class_data: Dict[str, Any], course_id: str,
                   school_id: str, term_id: str) -> OneRosterClass:
        """Add a class (section) to the export."""
        cls = OneRosterClass(
            sourcedId=f"CLS-{class_data.get('id', '')}",
            title=class_data.get("name", ""),
            classCode=class_data.get("section_code", ""),
            courseSourcedId=course_id,
            schoolSourcedId=school_id,
            termSourcedIds=term_id,
            periods=str(class_data.get("period", "")),
            location=class_data.get("room", "")
        )
        self.classes.append(cls)
        return cls

    def add_enrollment(self, student_id: str, class_id: str, school_id: str,
                       role: str = "student", start_date: str = "", end_date: str = "") -> OneRosterEnrollment:
        """Add an enrollment record."""
        enrollment = OneRosterEnrollment(
            sourcedId=f"ENR-{student_id}-{class_id}",
            classSourcedId=class_id,
            schoolSourcedId=school_id,
            userSourcedId=student_id,
            role=role,
            beginDate=start_date,
            endDate=end_date
        )
        self.enrollments.append(enrollment)
        return enrollment

    def add_academic_session(self, session_data: Dict[str, Any]) -> OneRosterAcademicSession:
        """Add an academic session."""
        session = OneRosterAcademicSession(
            sourcedId=str(session_data.get("id", "")),
            title=session_data.get("name", ""),
            type=session_data.get("type", "term"),
            startDate=str(session_data.get("start_date", "")),
            endDate=str(session_data.get("end_date", "")),
            schoolYear=session_data.get("school_year", ""),
            parentSourcedId=session_data.get("parent_id", "")
        )
        self.academic_sessions.append(session)
        return session

    def _generate_csv(self, records: List[Any], headers: List[str]) -> str:
        """Generate CSV content from records."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
        return output.getvalue()

    def export_users_csv(self) -> str:
        """Export users to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "enabledUser", "role",
                   "username", "givenName", "familyName", "middleName", "email",
                   "phone", "grades", "orgSourcedIds", "identifier"]
        return self._generate_csv(self.users, headers)

    def export_orgs_csv(self) -> str:
        """Export organizations to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "name", "type",
                   "identifier", "parentSourcedId"]
        return self._generate_csv(self.orgs, headers)

    def export_courses_csv(self) -> str:
        """Export courses to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "title", "courseCode",
                   "grades", "orgSourcedId", "subjectCodes"]
        return self._generate_csv(self.courses, headers)

    def export_classes_csv(self) -> str:
        """Export classes to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "title", "classCode",
                   "classType", "courseSourcedId", "schoolSourcedId", "termSourcedIds",
                   "grades", "periods", "location"]
        return self._generate_csv(self.classes, headers)

    def export_enrollments_csv(self) -> str:
        """Export enrollments to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "classSourcedId",
                   "schoolSourcedId", "userSourcedId", "role", "primary",
                   "beginDate", "endDate"]
        return self._generate_csv(self.enrollments, headers)

    def export_academic_sessions_csv(self) -> str:
        """Export academic sessions to CSV."""
        headers = ["sourcedId", "status", "dateLastModified", "title", "type",
                   "startDate", "endDate", "parentSourcedId", "schoolYear"]
        return self._generate_csv(self.academic_sessions, headers)

    def export_all(self) -> Dict[str, str]:
        """Export all OneRoster files."""
        return {
            "users.csv": self.export_users_csv(),
            "orgs.csv": self.export_orgs_csv(),
            "courses.csv": self.export_courses_csv(),
            "classes.csv": self.export_classes_csv(),
            "enrollments.csv": self.export_enrollments_csv(),
            "academicSessions.csv": self.export_academic_sessions_csv(),
        }

    def get_manifest(self) -> Dict[str, Any]:
        """Get OneRoster manifest."""
        return {
            "manifest.version": "1.0",
            "oneroster.version": "1.2",
            "file.academicSessions": "bulk" if self.academic_sessions else "absent",
            "file.categories": "absent",
            "file.classes": "bulk" if self.classes else "absent",
            "file.classResources": "absent",
            "file.courses": "bulk" if self.courses else "absent",
            "file.courseResources": "absent",
            "file.demographics": "absent",
            "file.enrollments": "bulk" if self.enrollments else "absent",
            "file.lineItemLearningObjectiveIds": "absent",
            "file.lineItems": "absent",
            "file.orgs": "bulk" if self.orgs else "absent",
            "file.resources": "absent",
            "file.results": "absent",
            "file.resultLearningObjectiveIds": "absent",
            "file.users": "bulk" if self.users else "absent",
            "file.userProfiles": "absent",
            "file.userResources": "absent",
        }

    def get_stats(self) -> Dict[str, int]:
        """Get export statistics."""
        return {
            "users": len(self.users),
            "students": sum(1 for u in self.users if u.role == "student"),
            "guardians": sum(1 for u in self.users if u.role == "guardian"),
            "teachers": sum(1 for u in self.users if u.role == "teacher"),
            "organizations": len(self.orgs),
            "courses": len(self.courses),
            "classes": len(self.classes),
            "enrollments": len(self.enrollments),
            "academic_sessions": len(self.academic_sessions),
        }
