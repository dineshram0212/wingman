import datetime
import os.path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# from wingman.plugins.tool_decorator import tool

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class Calendar:

    def __init__(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

        try:
            self.service = build("calendar", "v3", credentials=creds)
        except HttpError as error:
            print(f"An error occurred: {error}")

    # @tool
    def get_events(self, maxResults: int = 10, calendarId: str = "primary"):
        """
        Fetches upcoming events from the user's Google Calendar.

        :param maxResults (int): Number of upcoming events to retrieve. Default is 10.
        :param calendarId (str): Calendar ID to fetch events from. Default is 'primary'.

        Returns:
            list: A list of upcoming events with start time and summary.
        """
        import datetime

        now = datetime.datetime.utcnow().isoformat() + "Z"  # RFC3339 UTC timestamp
        print(f"Getting the upcoming {maxResults} events...")

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendarId,
                    timeMin=now,
                    maxResults=maxResults,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return []

            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(start, event.get("summary", "No Title"))

            return events

        except Exception as e:
            print("An error occurred while fetching events:", str(e))
            return []


    # @tool
    def create_event(self, summary: str, description: str, start_time: str, end_time: str, timezone: str='UTC', attendees: List[str]=None, location: str=None, calendarId: str = "primary"):
        """
        Creates a new event in the user's primary calendar.

        :param summary (str): Title of the event.
        :param description (str): Description of the event.
        :param start_time (str): Start time in RFC3339 format (e.g. "2025-03-28T09:00:00").
        :param end_time (str): End time in RFC3339 format (e.g. "2025-03-28T10:00:00").
        :param timezone (str): Time zone (default is 'UTC').
        :param attendees (list): List of attendee email addresses (optional).
        :param location (str): Event location (optional).
        :param calendarId (str): Calendar ID to fetch events from. Default is 'primary'.

        Returns:
            dict: Created event details.
        """
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
        }

        if attendees:
            event_body['attendees'] = [{'email': email} for email in attendees]
        
        if location:
            event_body['location'] = location

        event = self.service.events().insert(
            calendarId='primary',
            body=event_body,
            sendUpdates='all', 
        ).execute()

        print(f"Event created: {event.get('htmlLink')}")
        return event


    
        
if __name__ == '__main__':
    cal = Calendar()
    cal.create_event(
    summary="Project Sync-up Meeting",
    description="Weekly sync-up to discuss project status and blockers.",
    start_time="2025-03-28T15:00:00", 
    end_time="2025-03-28T16:00:00",
    timezone="Asia/Kolkata",
    attendees=["alice@example.com", "bob@example.com"],
    location="Zoom / Google Meet"
)

