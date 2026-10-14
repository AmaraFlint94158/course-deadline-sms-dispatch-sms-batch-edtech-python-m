import os
from datetime import datetime, timedelta, timezone

from course_campaign.campaign_service import dispatch_campaign
from course_campaign.infrai_client import InfraiClient
from course_campaign.models import CampaignRequest, LearnerDeadline


def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    phone = os.environ.get("DEMO_PHONE")
    if not api_key or not phone:
        raise SystemExit("Set INFRAI_API_KEY and DEMO_PHONE")

    now = datetime.now(timezone.utc)
    campaign = CampaignRequest(
        campaign_id=f"course-reminder-{now:%Y%m%d%H%M}",
        course_name="Python Foundations",
        learners=[
            LearnerDeadline(
                learner_id="demo-learner",
                phone=phone,
                due_at=now + timedelta(hours=6),
            )
        ],
    )
    client = InfraiClient(api_key=api_key)
    try:
        print(dispatch_campaign(campaign, client, now=now).model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

