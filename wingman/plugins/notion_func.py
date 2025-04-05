import os
from dotenv import load_dotenv
import requests
from typing import List, Dict
from wingman.utils.tool_decorator import tool
load_dotenv()

class NotionClient:
    def __init__(self, version: str = "2022-06-28"):
        self.token = os.getenv('NOTION_TOKEN')
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": version,
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.notion.com/v1"

    @tool
    def create_note_page(self, parent_id: str, title: str, content: str) -> dict:
        """
        Create a Notion page with a single text note.

        :param parent_id: The ID of the parent page where this note should be created.
        :param title: The title of the note page.
        :param content: The paragraph content of the note.
        :return: The response from the Notion API as a dictionary.
        """
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": [
                    {"text": {"content": title}}
                ]
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content}}
                        ]
                    }
                }
            ]
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    @tool
    def create_todo_page(self, parent_id: str, title: str, tasks: List[str]) -> dict:
        """
        Create a Notion page with a list of to-do items.

        :param parent_id: The ID of the parent page where the to-do page will be created.
        :param title: The title of the to-do page.
        :param tasks: A list of task strings to be added as to-do items.
        :return: The response from the Notion API as a dictionary.
        """
        url = f"{self.base_url}/pages"
        todo_blocks = [
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": task}}],
                    "checked": False
                }
            } for task in tasks
        ]
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": [
                    {"text": {"content": title}}
                ]
            },
            "children": todo_blocks
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    @tool
    def create_dashboard(self, parent_id: str, title: str, sections: List[Dict[str, str]]) -> dict:
        """
        Create a Notion page that functions as a dashboard, with multiple section headings and content.

        :param parent_id: The ID of the parent page where the dashboard will be created.
        :param title: The title of the dashboard page.
        :param sections: A list of dictionaries with 'title' and 'content' keys representing sections of the dashboard.
        :return: The response from the Notion API as a dictionary.
        """
        url = f"{self.base_url}/pages"
        blocks = []
        for section in sections:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": section['title']}}
                    ]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": section['content']}}
                    ]
                }
            })
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": [
                    {"text": {"content": title}}
                ]
            },
            "children": blocks
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    @tool
    def search_pages(self, query: str) -> dict:
        """
        Search for pages in the Notion workspace matching a specific query string.

        :param query: The search keyword or phrase.
        :return: The response from the Notion API containing matched pages.
        """
        url = f"{self.base_url}/search"
        payload = {"query": query}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
