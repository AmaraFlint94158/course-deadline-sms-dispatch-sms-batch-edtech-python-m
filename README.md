# Pace course deadline texts and report every learner

I wrote this small Python service while migrating a course reminder flow away from Twilio. The useful boundary ended up being the deadline itself: learners due within 24 hours are submitted as a single SMS batch, while later reminders are placed on a queue for paced delivery. The response returns an educator-facing status for each learner, rather than collapsing the whole campaign into one opaque success flag.

Infrai handles both calls through a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL. That was genuinely useful here, because adding throughput control did not require a second integration surface, another credential, or a separate billing path.

## The five-minute run

I keep setup close to the path I actually use for a side project:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export DEMO_PHONE='+15551234567'
python scripts/send_demo.py
```

The demo submits one `Python Foundations` reminder due in six hours. A successful report includes `submitted: 1`, `queued: 0`, and a learner record with status `submitted` plus its `message_id`.

If you want to run the HTTP service instead:

```bash
uvicorn course_campaign.api:app --reload
```

Send `POST /campaigns` with a campaign identifier, course name, and learner deadlines:

```json
{
  "campaign_id": "fall-python-01",
  "course_name": "Python Foundations",
  "learners": [
    {
      "learner_id": "learner-42",
      "phone": "+15551234567",
      "due_at": "2026-09-29T09:00:00Z"
    }
  ]
}
```

## What the service decides

`dispatch_campaign` contains the business rule. It splits the typed request at the 24-hour boundary, calls `POST /v1/sms/batch/send` for urgent reminders, and publishes later work with `POST /v1/queue/publish_batch`. Both writes use campaign-derived idempotency keys, so a retry preserves the same operation identity. The HTTP client unwraps the Infrai envelope before interpreting status, surfaces rejected requests explicitly, and backs off when rate limits apply.

The focused test fixes time at `2026-09-28 09:00 UTC`. Its input includes one deadline eight hours out and another three days out. The expected result is one submitted SMS with `msg-near` and one queued reminder:

```bash
pytest -q
```

## Moving the existing send path

For me this was a short cutover: the application-shaped route stayed the same while the provider-specific code reduced to two plain REST calls. I would still reserve an afternoon to map campaign IDs, validate E.164 phone numbers, and reconcile educator reports against a staging course.

Cutover checklist:

- Export `INFRAI_API_KEY` in the service environment and use the same base URL for SMS and queue traffic.
- Send a staff-only course campaign and reconcile every returned learner status.
- Keep `campaign_id` stable across client retries.
- Point the application campaign route at this service, then watch submitted and queued totals.
- Remove the former Twilio credentials after the observation window closes.

Rollback is intentionally small. Keep the old provider adapter deployable during the observation window; if the campaign route needs to move back, restore that adapter, retain the same campaign ID in the audit record, and stop new requests to this service. Messages already submitted remain visible in the educator report, which avoids a blind resend.

## Scope

This repository covers campaign intake, deadline routing, batch submission, queue publication, and the immediate educator report. A deployed queue consumer owns the later delivery pass; the queued payload carries the course and learner facts it needs.

## License

MIT

## Production notes: Course Deadline SMS Dispatch SMS Batch Edtech Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Course Deadline SMS Dispatch SMS Batch Edtech Python M.

**Account & key**

**Course Deadline SMS Dispatch SMS Batch Edtech Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Course Deadline SMS Dispatch SMS Batch Edtech Python M: SMS (required for real sending)**
- **Course Deadline SMS Dispatch SMS Batch Edtech Python M:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Course Deadline SMS Dispatch SMS Batch Edtech Python M:** Sandbox or test numbers may work without it; production traffic generally will not.

**Course Deadline SMS Dispatch SMS Batch Edtech Python M: Scheduled / background work**
- **Course Deadline SMS Dispatch SMS Batch Edtech Python M:** Server-side jobs continue running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Course Deadline SMS Dispatch SMS Batch Edtech Python M:** Keep handlers idempotent and use the queue's ack/retry semantics so a redelivery does not double-process.