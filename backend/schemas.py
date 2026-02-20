import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class ScheduleRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=20)


# Right now it only works for calling US candidates, but we can expand it later if needed.
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = value.strip()
        allowed = "+0123456789 -()"
        if not all(ch in allowed for ch in cleaned):
            raise ValueError("Phone number contains invalid characters.")
        digits = re.sub(r"\D", "", cleaned)
        digit_count = len(digits)
        if digit_count == 10:
            return cleaned
        if digit_count == 11 and digits.startswith("1"):
            return cleaned
        raise ValueError("Phone number must be a valid US number (10 digits or +1 country code).")


class ScheduleResponse(BaseModel):
    status: str
    call_id: str | None = None


# Future use: We can re-enable when candidate persistence/reporting is added.
# class CandidateRecord(BaseModel):
#     name: str
#     email: EmailStr
#     phone: str
#     created_at: datetime
