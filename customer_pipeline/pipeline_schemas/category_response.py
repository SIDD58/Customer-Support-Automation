from pydantic import BaseModel, Field
from typing import Literal

# Define the expected structure
class CategoryResponse(BaseModel):
    category: Literal["SHIPPING", "REFUND", "GENERAL"] = Field(
        description="The classification of the customer inquiry"
    )
    reasoning: str = Field(description="Brief explanation of why this category was chosen")