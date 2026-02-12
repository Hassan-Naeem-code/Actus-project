"""
Identity Resolution Module
Based on DMaaS Playbook Section 1.1.1

Provides:
- Golden Identifier Strategy: Map multiple IDs (student_id, state_id, email)
- Deterministic Matching: Exact match rules (StateID + DOB, Name + DOB)
- Guardian/Household Graph: Link students to guardians, handle custody
- Duplicate Detection: Cross-source identity resolution
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Tuple, Set, Any
from enum import Enum
import hashlib
import re


class MatchConfidence(Enum):
    """Confidence levels for identity matches."""
    EXACT = "exact"  # 100% match on unique identifier
    HIGH = "high"  # 95%+ match on multiple fields
    MEDIUM = "medium"  # 80%+ match, needs review
    LOW = "low"  # Possible match, requires manual review
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    """Result of an identity match operation."""
    source_id: str
    target_id: str
    confidence: MatchConfidence
    match_score: float
    matched_fields: List[str]
    mismatched_fields: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "confidence": self.confidence.value,
            "match_score": self.match_score,
            "matched_fields": self.matched_fields,
            "mismatched_fields": self.mismatched_fields,
        }


@dataclass
class GoldenRecord:
    """
    A golden record representing a unified identity across sources.
    """
    golden_id: str
    primary_source: str
    source_ids: Dict[str, str] = field(default_factory=dict)  # source -> id
    first_name: str = ""
    last_name: str = ""
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    state_id: Optional[str] = None
    merged_from: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def add_source_id(self, source: str, source_id: str):
        """Add a source system ID to this golden record."""
        self.source_ids[source] = source_id
        if source not in self.merged_from:
            self.merged_from.append(source)

    def generate_golden_id(self) -> str:
        """Generate a unique golden ID based on key attributes."""
        key = f"{self.first_name}|{self.last_name}|{self.date_of_birth}|{self.state_id}"
        return "GR-" + hashlib.md5(key.encode()).hexdigest()[:12].upper()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "golden_id": self.golden_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": str(self.date_of_birth) if self.date_of_birth else None,
            "email": self.email,
            "state_id": self.state_id,
            "source_ids": self.source_ids,
            "merged_from": self.merged_from,
        }


@dataclass
class HouseholdGraph:
    """
    Graph structure for managing household relationships.
    """
    households: Dict[str, List[str]] = field(default_factory=dict)  # household_id -> member_ids
    person_to_household: Dict[str, str] = field(default_factory=dict)  # person_id -> household_id
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    def add_household(self, household_id: str, members: List[str]):
        """Add a household with its members."""
        self.households[household_id] = members
        for member in members:
            self.person_to_household[member] = household_id

    def add_relationship(self, guardian_id: str, student_id: str, relationship_type: str,
                         custody_type: str = "Full", emergency_priority: int = 0):
        """Add a guardian-student relationship."""
        self.relationships.append({
            "guardian_id": guardian_id,
            "student_id": student_id,
            "relationship_type": relationship_type,
            "custody_type": custody_type,
            "emergency_priority": emergency_priority,
        })

    def get_guardians_for_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all guardians for a student."""
        return [r for r in self.relationships if r["student_id"] == student_id]

    def get_students_for_guardian(self, guardian_id: str) -> List[Dict[str, Any]]:
        """Get all students for a guardian."""
        return [r for r in self.relationships if r["guardian_id"] == guardian_id]


class IdentityResolver:
    """
    Identity resolution engine for cross-source matching.
    """

    def __init__(self):
        self.golden_records: Dict[str, GoldenRecord] = {}
        self.source_to_golden: Dict[str, Dict[str, str]] = {}  # source -> {source_id -> golden_id}
        self.duplicates: List[MatchResult] = []
        self.household_graph = HouseholdGraph()

    def normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        if not name:
            return ""
        # Strip whitespace, convert to lowercase, remove special chars
        normalized = re.sub(r'[^\w\s]', '', str(name).strip().lower())
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def normalize_email(self, email: str) -> str:
        """Normalize an email for comparison."""
        if not email:
            return ""
        return str(email).strip().lower()

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to digits only."""
        if not phone:
            return ""
        return re.sub(r'[^\d]', '', str(phone))

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using Levenshtein-like scoring."""
        n1 = self.normalize_name(name1)
        n2 = self.normalize_name(name2)

        if n1 == n2:
            return 1.0

        if not n1 or not n2:
            return 0.0

        # Simple character overlap scoring
        set1 = set(n1)
        set2 = set(n2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def match_records(self, record1: Dict[str, Any], record2: Dict[str, Any],
                      source1: str = "source1", source2: str = "source2") -> MatchResult:
        """
        Match two records and determine if they represent the same person.
        Uses deterministic matching rules from the playbook.
        """
        matched_fields = []
        mismatched_fields = []
        score = 0.0

        # Rule 1: State ID exact match (highest weight)
        if record1.get("state_id") and record2.get("state_id"):
            if str(record1["state_id"]).strip() == str(record2["state_id"]).strip():
                matched_fields.append("state_id")
                score += 0.4
            else:
                mismatched_fields.append("state_id")

        # Rule 2: Email exact match
        email1 = self.normalize_email(record1.get("email", ""))
        email2 = self.normalize_email(record2.get("email", ""))
        if email1 and email2:
            if email1 == email2:
                matched_fields.append("email")
                score += 0.25
            else:
                mismatched_fields.append("email")

        # Rule 3: Name matching
        fn1 = self.normalize_name(record1.get("first_name", ""))
        fn2 = self.normalize_name(record2.get("first_name", ""))
        ln1 = self.normalize_name(record1.get("last_name", ""))
        ln2 = self.normalize_name(record2.get("last_name", ""))

        if fn1 == fn2 and fn1:
            matched_fields.append("first_name")
            score += 0.15
        elif fn1 and fn2:
            mismatched_fields.append("first_name")

        if ln1 == ln2 and ln1:
            matched_fields.append("last_name")
            score += 0.15
        elif ln1 and ln2:
            mismatched_fields.append("last_name")

        # Rule 4: Date of birth matching
        dob1 = record1.get("date_of_birth") or record1.get("dob")
        dob2 = record2.get("date_of_birth") or record2.get("dob")
        if dob1 and dob2:
            if str(dob1) == str(dob2):
                matched_fields.append("date_of_birth")
                score += 0.15
            else:
                mismatched_fields.append("date_of_birth")

        # Rule 5: Phone matching
        phone1 = self.normalize_phone(record1.get("phone", ""))
        phone2 = self.normalize_phone(record2.get("phone", ""))
        if phone1 and phone2 and len(phone1) >= 10 and len(phone2) >= 10:
            if phone1[-10:] == phone2[-10:]:  # Compare last 10 digits
                matched_fields.append("phone")
                score += 0.1

        # Determine confidence level
        if "state_id" in matched_fields:
            confidence = MatchConfidence.EXACT
        elif score >= 0.8:
            confidence = MatchConfidence.HIGH
        elif score >= 0.5:
            confidence = MatchConfidence.MEDIUM
        elif score >= 0.3:
            confidence = MatchConfidence.LOW
        else:
            confidence = MatchConfidence.NO_MATCH

        return MatchResult(
            source_id=f"{source1}:{record1.get('student_id', record1.get('id', 'unknown'))}",
            target_id=f"{source2}:{record2.get('student_id', record2.get('id', 'unknown'))}",
            confidence=confidence,
            match_score=score,
            matched_fields=matched_fields,
            mismatched_fields=mismatched_fields
        )

    def find_duplicates(self, records: List[Dict[str, Any]], source: str = "default") -> List[MatchResult]:
        """
        Find duplicate records within a dataset.
        Returns list of potential duplicate pairs.
        """
        duplicates = []

        for i, rec1 in enumerate(records):
            for j, rec2 in enumerate(records[i + 1:], start=i + 1):
                result = self.match_records(rec1, rec2, source, source)
                if result.confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH, MatchConfidence.MEDIUM]:
                    duplicates.append(result)

        self.duplicates.extend(duplicates)
        return duplicates

    def resolve_identity(self, record: Dict[str, Any], source: str) -> Tuple[str, bool]:
        """
        Resolve a record's identity, creating or merging with a golden record.
        Returns (golden_id, is_new_record).
        """
        # Check if we already have a mapping for this source ID
        source_id = str(record.get("student_id", record.get("id", "")))
        if source in self.source_to_golden:
            if source_id in self.source_to_golden[source]:
                return self.source_to_golden[source][source_id], False

        # Try to match against existing golden records
        for golden_id, golden in self.golden_records.items():
            # Create a dict from golden record for comparison
            golden_dict = {
                "first_name": golden.first_name,
                "last_name": golden.last_name,
                "email": golden.email,
                "state_id": golden.state_id,
                "date_of_birth": golden.date_of_birth,
            }
            result = self.match_records(record, golden_dict, source, "golden")

            if result.confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH]:
                # Merge with existing golden record
                golden.add_source_id(source, source_id)

                # Update source mapping
                if source not in self.source_to_golden:
                    self.source_to_golden[source] = {}
                self.source_to_golden[source][source_id] = golden_id

                return golden_id, False

        # Create new golden record
        golden = GoldenRecord(
            golden_id="",
            primary_source=source,
            first_name=str(record.get("first_name", "")).strip().title(),
            last_name=str(record.get("last_name", "")).strip().title(),
            email=record.get("email"),
            state_id=record.get("state_id"),
            date_of_birth=record.get("date_of_birth"),
        )
        golden.add_source_id(source, source_id)
        golden.golden_id = golden.generate_golden_id()

        self.golden_records[golden.golden_id] = golden

        if source not in self.source_to_golden:
            self.source_to_golden[source] = {}
        self.source_to_golden[source][source_id] = golden.golden_id

        return golden.golden_id, True

    def build_household_graph(self, guardians: List[Dict[str, Any]]) -> HouseholdGraph:
        """
        Build the household graph from guardian data.
        """
        for guardian in guardians:
            guardian_id = str(guardian.get("guardian_id", ""))
            student_ids_raw = guardian.get("student_ids", "")

            # Parse student IDs (may be comma-separated)
            if isinstance(student_ids_raw, str):
                student_ids = [s.strip() for s in student_ids_raw.split(",")]
            else:
                student_ids = [str(student_ids_raw)]

            relationship_type = guardian.get("relationship", "Guardian")
            custody_type = guardian.get("custody_type", "Full")
            emergency_priority = int(guardian.get("emergency_priority", 0))

            for student_id in student_ids:
                if student_id:
                    self.household_graph.add_relationship(
                        guardian_id=guardian_id,
                        student_id=student_id,
                        relationship_type=relationship_type,
                        custody_type=custody_type,
                        emergency_priority=emergency_priority
                    )

        return self.household_graph

    def get_identity_stats(self) -> Dict[str, Any]:
        """Get statistics about identity resolution."""
        return {
            "total_golden_records": len(self.golden_records),
            "total_source_mappings": sum(len(m) for m in self.source_to_golden.values()),
            "sources_processed": list(self.source_to_golden.keys()),
            "duplicates_found": len(self.duplicates),
            "high_confidence_matches": sum(
                1 for d in self.duplicates
                if d.confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH]
            ),
            "relationships": len(self.household_graph.relationships),
        }

    def get_duplicate_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of found duplicates."""
        return [d.to_dict() for d in self.duplicates]
