from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from .models import CampaignReport, CampaignRequest, LearnerStatus


class CampaignGateway(Protocol):
    def send_sms_batch(
        self, messages: list[dict[str, str]], idempotency_key: str
    ) -> dict[str, Any]:
        pass

    def publish_queue_batch(
        self, queue: str, messages: list[dict[str, Any]], idempotency_key: str
    ) -> dict[str, Any]:
        pass


def dispatch_campaign(
    campaign: CampaignRequest,
    gateway: CampaignGateway,
    now: datetime | None = None,
) -> CampaignReport:
    clock = now or datetime.now(timezone.utc)
    cutoff = clock + timedelta(hours=24)
    immediate = [learner for learner in campaign.learners if learner.due_at <= cutoff]
    paced = [learner for learner in campaign.learners if learner.due_at > cutoff]
    statuses: list[LearnerStatus] = []

    if immediate:
        data = gateway.send_sms_batch(
            [
                {
                    "to": learner.phone,
                    "message": (
                        f"{campaign.course_name} is due "
                        f"{learner.due_at.astimezone(timezone.utc):%Y-%m-%d %H:%M} UTC."
                    ),
                }
                for learner in immediate
            ],
            idempotency_key=f"{campaign.campaign_id}:sms",
        )
        results = data.get("messages", [])
        for index, learner in enumerate(immediate):
            result = results[index] if index < len(results) else {}
            statuses.append(
                LearnerStatus(
                    learner_id=learner.learner_id,
                    status="submitted",
                    message_id=result.get("message_id"),
                )
            )

    if paced:
        gateway.publish_queue_batch(
            queue="course-deadline-sms",
            messages=[
                {
                    "payload": {
                        "campaign_id": campaign.campaign_id,
                        "learner_id": learner.learner_id,
                        "phone": learner.phone,
                        "course_name": campaign.course_name,
                        "due_at": learner.due_at.isoformat(),
                    }
                }
                for learner in paced
            ],
            idempotency_key=f"{campaign.campaign_id}:queue",
        )
        statuses.extend(
            LearnerStatus(learner_id=learner.learner_id, status="queued")
            for learner in paced
        )

    return CampaignReport(
        campaign_id=campaign.campaign_id,
        submitted=len(immediate),
        queued=len(paced),
        learners=statuses,
    )
