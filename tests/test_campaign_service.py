from datetime import datetime, timedelta, timezone
from typing import Any

from course_campaign.campaign_service import dispatch_campaign
from course_campaign.models import CampaignRequest, LearnerDeadline


class RecordingGateway:
    def __init__(self) -> None:
        self.sms_messages: list[dict[str, str]] = []
        self.queued_messages: list[dict[str, Any]] = []

    def send_sms_batch(
        self, messages: list[dict[str, str]], idempotency_key: str
    ) -> dict[str, Any]:
        self.sms_messages = messages
        assert idempotency_key == "fall-python:sms"
        return {"messages": [{"message_id": "msg-near"}]}

    def publish_queue_batch(
        self, queue: str, messages: list[dict[str, Any]], idempotency_key: str
    ) -> dict[str, Any]:
        assert queue == "course-deadline-sms"
        assert idempotency_key == "fall-python:queue"
        self.queued_messages = messages
        return {"published": len(messages)}


def test_near_deadline_is_sent_and_later_deadline_is_paced() -> None:
    now = datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc)
    campaign = CampaignRequest(
        campaign_id="fall-python",
        course_name="Python Foundations",
        learners=[
            LearnerDeadline(
                learner_id="near",
                phone="+15550000001",
                due_at=now + timedelta(hours=8),
            ),
            LearnerDeadline(
                learner_id="later",
                phone="+15550000002",
                due_at=now + timedelta(days=3),
            ),
        ],
    )
    gateway = RecordingGateway()

    report = dispatch_campaign(campaign, gateway, now=now)

    assert report.submitted == 1
    assert report.queued == 1
    assert report.learners[0].model_dump() == {
        "learner_id": "near",
        "status": "submitted",
        "message_id": "msg-near",
    }
    assert report.learners[1].status == "queued"
    assert gateway.sms_messages[0]["to"] == "+15550000001"
    assert gateway.queued_messages[0]["payload"]["learner_id"] == "later"

