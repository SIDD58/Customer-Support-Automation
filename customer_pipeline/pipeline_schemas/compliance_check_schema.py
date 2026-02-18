from pydantic import BaseModel, Field

class ComplianceCheck(BaseModel):
    is_compliant: bool = Field(description="True if the draft follows all business rules.")
    feedback: str = Field(description="If not compliant, explain why (e.g., 'Promised a refund').")