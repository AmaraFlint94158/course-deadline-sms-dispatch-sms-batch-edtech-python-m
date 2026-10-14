import os

from fastapi import FastAPI, HTTPException

from .campaign_service import dispatch_campaign
from .infrai_client import InfraiClient, InfraiError
from .models import CampaignReport, CampaignRequest

app = FastAPI(title="Course deadline campaign")


@app.post("/campaigns", response_model=CampaignReport)
def create_campaign(campaign: CampaignRequest) -> CampaignReport:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key=api_key)
    try:
        return dispatch_campaign(campaign, client)
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=error.detail) from error
    finally:
        client.close()

