import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#################
# CONFIGURATION #
#################

# = {{{

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# = }}}

####################
# SCRAPE FUNCTIONS #
####################

# = {{{

def get_calendar_service():
  """Handles local authentication with Google OAuth2."""
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      if not os.path.exists("credentials.json"):
        raise FileNotFoundError("credentials.json not found!")

      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
      token.write(creds.to_json())

  return build("calendar", "v3", credentials=creds)


def get_today_events_all_calendars():
  try:
    service = get_calendar_service()

    # Get local timezone start and end of current day
    now = datetime.datetime.now().astimezone()
    start_of_day = (
        now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    )
    end_of_day = (
        now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    )

    today_str = now.strftime("%B %d, %Y")
    print("=" * 65)
    print(f"📅 TODAY'S SCHEDULE ACROSS ALL CALENDARS ({today_str})")
    print("=" * 65)

    # 1. Fetch list of all calendars the account has access to
    calendar_list = service.calendarList().list().execute().get("items", [])

    all_events = []

    # 2. Iterate through each calendar and gather today's events
    for cal in calendar_list:
      # Skip hidden/unselected calendars if desired
      if cal.get("selected") is False:
        continue

      cal_id = cal["id"]
      cal_summary = cal.get("summary", cal_id)

      events_result = (
          service.events()
          .list(
              calendarId=cal_id,
              timeMin=start_of_day,
              timeMax=end_of_day,
              singleEvents=True,
              orderBy="startTime",
          )
          .execute()
      )

      events = events_result.get("items", [])

      for event in events:
        all_events.append({"calendar": cal_summary, "event": event})

    if not all_events:
      print("No events scheduled for today across any calendars.")
      return

    # Sort all aggregated events by start time
    def get_event_time(item):
      start = item["event"]["start"]
      return start.get("dateTime", start.get("date"))

    all_events.sort(key=get_event_time)

    # 3. Print combined schedule
    for item in all_events:
      event = item["event"]
      cal_name = item["calendar"]

      start = event["start"].get("dateTime", event["start"].get("date"))
      summary = event.get("summary", "(No Title)")
      location = event.get("location", "")

      if "T" in start:
        dt = datetime.datetime.fromisoformat(start)
        time_str = dt.strftime("%I:%M %p")
      else:
        time_str = "All Day"

      print(f"• [{time_str}] {summary}  (Calendar: {cal_name})")
      if location:
        print(f"  📍 {location}")
      print()

  except HttpError as error:
    print(f"An API error occurred: {error}")

# = }}}

if __name__ == "__main__":
  get_today_events_all_calendars()
