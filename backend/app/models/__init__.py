"""Import all models so Alembic + Base.metadata see them."""
from app.models.assessment import Assessment, AssessmentResult, Question
from app.models.concept import Concept, concept_prerequisites
from app.models.course import Course, Enrollment
from app.models.enums import (
    ActivityType,
    AssessmentType,
    MasteryStatus,
    PedagogyStrategy,
    RemediationStatus,
    UserRole,
)
from app.models.lead import Lead
from app.models.lti import (
    LtiDeployment,
    LtiNonce,
    LtiRegistration,
    LtiToolKey,
)
from app.models.mastery import ConceptMastery
from app.models.material import CourseMaterial
from app.models.remediation import (
    RemediationActivity,
    RemediationModule,
    StudentResponse,
    TutorMessage,
)
from app.models.sage import SageAnnouncement
from app.models.tenant import Tenant
from app.models.user import User

__all__ = [
    "Assessment", "AssessmentResult", "Question", "Concept", "concept_prerequisites",
    "Course", "Enrollment", "ConceptMastery", "CourseMaterial", "RemediationActivity",
    "RemediationModule", "StudentResponse", "TutorMessage", "User", "ActivityType",
    "AssessmentType", "MasteryStatus", "PedagogyStrategy", "RemediationStatus", "UserRole",
    "LtiRegistration", "LtiDeployment", "LtiNonce", "LtiToolKey", "Lead", "Tenant",
    "SageAnnouncement",
]
