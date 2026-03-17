---
name: calendar-booking
description: "Parse natural language date/time from user messages, query Google Calendar
  for available slots, create calendar events, and send booking confirmations.
  Use when: user wants to book/schedule an appointment, mentions keywords like
  預約, 約時間, 排時間, 訂時間, 安排, book, schedule, appointment, reserve,
  or when intent is clearly to arrange a meeting/service time.
  NOT for: querying existing calendar events, modifying/cancelling bookings,
  recurring schedules, or general date questions without booking intent.
  Requires: Google Calendar API credentials configured."
metadata:
  openclaw:
    emoji: "📅"
    requires:
      bins: ["python3"]
---

# Calendar Booking Skill

## Overview

Handle the full booking flow: parse intent → extract date/time → query free slots → present options → confirm with user → create event → return confirmation with Calendar link → write CRM record.

## Configuration

Load `references/calendar_fields.json` at the start of any booking flow. This file defines:

- `business_name` — used in event titles
- `calendar_id` — target Google Calendar (e.g. "primary")
- `available_days` — which days accept bookings (e.g. Mon–Fri)
- `available_hours` — start/end times for bookings
- `default_duration_minutes` — fallback if user doesn't specify
- `booking_buffer_minutes` — minimum gap between events
- `event_title_format` — template for event titles
- `timezone` — all times in this timezone
- `confirmation_language` — reply language (zh-TW, en, ja, zh-CN)
- `credentials_file` — path to OAuth2 client secret JSON (relative to skill dir)
- `token_file` — path to cached OAuth2 token (relative to skill dir)

If `calendar_fields.json` has empty `business_name`, ask the user to configure it before proceeding.

### Credentials

This skill uses **OAuth2 Desktop (installed) app** credentials. The first run requires browser-based consent to authorize Google Calendar access. After authorization, the token is cached in `token_file` for subsequent calls.

Required Python packages:
```
pip install google-api-python-client google-auth-oauthlib
```

## Workflow

### Step 1: Detect Booking Intent

Trigger on keywords: 預約, 約時間, 排時間, 訂時間, 安排, 約一下, book, schedule, appointment, reserve.

Also trigger when user intent is clearly "arrange a meeting/service time" even without keywords.

**Do NOT trigger** when user is just asking about their schedule or mentioning dates casually.

### Step 2: Extract Parameters

From the user message, extract:

| Parameter | Required | Fallback |
|-----------|----------|----------|
| `date` | No — ask if missing | — |
| `time` | No — list all slots if missing | — |
| `duration` | No | `default_duration_minutes` from config |
| `client_name` | No — ask before creating event | — |
| `client_phone` | No | — |
| `subject` | No | auto-generate from `event_title_format` |
| `notes` | No | — |

Parse natural language dates relative to current date and `timezone` from config:
- "下週三" → next Wednesday
- "3/15" → March 15th
- "明天下午" → tomorrow afternoon

**One question at a time.** Never ask for multiple missing fields simultaneously.

### Step 3: Query Available Slots

Run the freebusy query script:

```bash
python3 {skill_dir}/scripts/gcal_freebusy.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --calendar-id "{calendar_id}" \
  --date "{YYYY-MM-DD}" \
  --timezone "{timezone}" \
  --start-hour "{available_hours.start}" \
  --end-hour "{available_hours.end}" \
  --duration "{duration_minutes}" \
  --buffer "{booking_buffer_minutes}"
```

Output: JSON array of available time slots.

### Step 4: Present Options

Show 2–3 available slots. Follow the reply format in `references/confirmation_prompts.md` § 2.1.

If no slots available on that day, show next available dates (§ 4.2).

### Step 5: Confirm Before Creating

After the user picks a slot, show a confirmation summary (§ 2.3) and ask for explicit "yes."

Collect `client_name` if not yet known.

### Step 6: Create Event

```bash
python3 {skill_dir}/scripts/gcal_create_event.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --calendar-id "{calendar_id}" \
  --title "{event_title}" \
  --start "{ISO-8601 start}" \
  --end "{ISO-8601 end}" \
  --timezone "{timezone}" \
  --description "{notes}" \
  --attendees "{comma-separated emails}"
```

Output: JSON with `event_id` and `calendar_link`.

### Step 7: Send Confirmation

Use the confirmation format from `references/confirmation_prompts.md` § 2.2. Include the Google Calendar link.

### Step 8: Write CRM Record

Append a JSON record to the CRM system (Module 03) with:

```json
{
  "timestamp": "{ISO-8601}",
  "type": "booking",
  "client_name": "{name}",
  "client_phone": "{phone}",
  "booking_date": "{YYYY-MM-DD}",
  "booking_time": "{HH:MM}",
  "duration_minutes": {N},
  "subject": "{title}",
  "status": "confirmed",
  "calendar_event_id": "{id}"
}
```

## Safety Constraints (Hard Rules)

1. **Create only** — never delete, modify, or bulk-operate on existing events
2. **Single calendar only** — only operate on the `calendar_id` from config
3. **Business hours only** — reject bookings outside `available_days` and `available_hours`
4. **Buffer enforced** — always maintain `booking_buffer_minutes` gap between events
5. **Confirmation required** — never create an event without explicit user confirmation

## Error Handling

| Situation | Action |
|-----------|--------|
| Requested time occupied | Show 3 nearest available slots (§ 4.1) |
| Non-business day | State business days, suggest nearest one (§ 4.3) |
| Outside business hours | State hours, suggest available slots (§ 4.4) |
| Missing date | Ask for date with examples (§ 4.5) |
| Missing time | List available slots for the date (§ 4.6) |
| Missing client name | Ask for name (§ 4.7) |
| API failure | Apologize, offer alternatives (§ 4.8) |

## References

- `references/calendar_fields.json` — Load at start of every booking flow. Contains all business configuration.
- `references/confirmation_prompts.md` — Load when composing reply messages. Contains system prompt, reply templates, and edge-case response formats for all supported languages.
