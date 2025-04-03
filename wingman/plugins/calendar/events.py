import os.path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from wingman.utils.tool_decorator import tool

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
                    os.path.join(os.path.dirname(__file__), "credentials.json")
                    , SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

        try:
            self.service = build("calendar", "v3", credentials=creds)
        except HttpError as error:
            print(f"An error occurred: {error}")

    @tool
    def get_events(self, maxResults: int = 10, calendarId: str = "primary"):
        """
        Fetches upcoming events from the user's Google Calendar.

        :param maxResults: Number of upcoming events to retrieve. Default is 10.
        :param calendarId: Calendar ID to fetch events from. Default is 'primary'.

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

            events = [(event["start"].get("dateTime", event["start"].get("date")), event.get("summary", "No Title")) for event in events]
            print("Events successfully fetched!")
            return events

        except Exception as e:
            print("An error occurred while fetching events:", str(e))
            return []


    @tool
    def create_event(self, summary: str, description: str, start_time: str, end_time: str, timezone: str='UTC', attendees: List[str]=None, location: str=None, calendarId: str = "primary"):
        """
        Creates a new event in the user's primary calendar.

        :param summary: Title of the event.
        :param description: Description of the event.
        :param start_time: Start time in RFC3339 format (e.g. "2025-03-28T09:00:00").
        :param end_time: End time in RFC3339 format (e.g. "2025-03-28T10:00:00").
        :param timezone: Time zone (default is 'UTC').
        :param attendees: List of attendee email addresses (optional).
        :param location: Event location (optional).
        :param calendarId: Calendar ID to fetch events from. Default is 'primary'.

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
