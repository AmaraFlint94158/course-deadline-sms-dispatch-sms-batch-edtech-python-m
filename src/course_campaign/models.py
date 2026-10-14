from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LearnerDeadline(BaseModel):
    learner_id: str = Field(min_length=1)
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    due_at: datetime


class CampaignRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    course_name: str = Field(min_length=1)
    learners: list[LearnerDeadline] = Field(min_length=1)


class LearnerStatus(BaseModel):
    learner_id: str
    status: Literal["submitted", "queued"]
    message_id: str | None = None


class CampaignReport(BaseModel):
    campaign_id: str
    submitted: int
    queued: int
    learners: list[LearnerStatus]

