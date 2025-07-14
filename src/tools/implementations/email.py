# src/tools/implementations/email.py
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path
from ..base import BaseTool
from ..registry import ToolRegistry


@ToolRegistry.register()
class GmailTool(BaseTool):
    description = "Send emails using Gmail API"
    parameters = {
        "to": {
            "type": "string",
            "description": "Recipient email address",
            "required": True,
        },
        "subject": {
            "type": "string",
            "description": "Email subject line",
            "required": True,
        },
        "body": {
            "type": "string",
            "description": "Email body content (supports HTML)",
            "required": True,
        },
        "is_html": {
            "type": "boolean",
            "description": "Whether the body contains HTML (default: False)",
            "required": False,
        },
        "cc": {
            "type": "string",
            "description": "CC recipient email addresses (comma-separated)",
            "required": False,
        },
        "bcc": {
            "type": "string",
            "description": "BCC recipient email addresses (comma-separated)",
            "required": False,
        },
    }

    def __init__(self):
        self.SCOPES = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
        ]
        self.credentials_file = "credentials.json"
        self.token_file = "token.pickle"
        self.service = None

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        creds = None

        # Check if we have a valid token
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Could not load existing token: {e}")
                # Remove corrupted token file
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise Exception(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Please download your OAuth2 credentials from Google Cloud Console "
                        "and save them as 'credentials.json' in the project root."
                    )

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )

                    # Try multiple ports to handle redirect URI issues
                    ports_to_try = [8080, 8081, 8082, 0]
                    creds = None

                    for port in ports_to_try:
                        try:
                            print(f"Trying authentication on port {port}...")
                            creds = flow.run_local_server(port=port, prompt="consent")
                            print(f"Authentication successful on port {port}")
                            break
                        except OSError as e:
                            if port == 0:  # Last resort
                                print("Trying random port...")
                                creds = flow.run_local_server(port=0, prompt="consent")
                                break
                            else:
                                print(f"Port {port} in use, trying next port...")
                                continue
                        except Exception as e:
                            if "redirect_uri_mismatch" in str(e).lower():
                                print(
                                    f"Redirect URI mismatch on port {port}, trying next port..."
                                )
                                continue
                            else:
                                raise e

                    if creds is None:
                        raise Exception("Failed to authenticate on any available port")

                    # Save the credentials for the next run
                    with open(self.token_file, "wb") as token:
                        pickle.dump(creds, token)

                except Exception as e:
                    error_msg = str(e)
                    if "redirect_uri_mismatch" in error_msg.lower():
                        raise Exception(
                            "OAuth2 redirect URI mismatch. Please configure your OAuth2 client in Google Cloud Console:\n"
                            "1. Go to APIs & Services > Credentials\n"
                            "2. Click on your OAuth 2.0 Client ID\n"
                            "3. Add these redirect URIs:\n"
                            "   - http://localhost:8080/\n"
                            "   - http://localhost:8081/\n"
                            "   - http://localhost:8082/\n"
                            "   - http://127.0.0.1:8080/\n"
                            "4. Click Save and try again"
                        )
                    else:
                        raise Exception(f"Authentication failed: {error_msg}")

        return creds

    def _create_message(
        self, sender, to, subject, body, is_html=False, cc=None, bcc=None
    ):
        """Create a message for an email"""
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc

        # Create the body of the message
        if is_html:
            part = MIMEText(body, "html")
        else:
            part = MIMEText(body, "plain")

        message.attach(part)

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw_message}

    async def execute(self, to, subject, body, is_html=False, cc=None, bcc=None):
        """Send an email using Gmail API"""
        try:
            # Authenticate
            creds = self._authenticate()
            service = build("gmail", "v1", credentials=creds)

            # Get the user's email address
            user_info = service.users().getProfile(userId="me").execute()
            sender = user_info["emailAddress"]

            # Create the message
            message = self._create_message(
                sender=sender,
                to=to,
                subject=subject,
                body=body,
                is_html=is_html,
                cc=cc,
                bcc=bcc,
            )

            # Send the message
            sent_message = (
                service.users().messages().send(userId="me", body=message).execute()
            )

            return f"Email sent successfully! Message ID: {sent_message['id']}"

        except Exception as e:
            return f"Error sending email: {str(e)}"

    def get_setup_instructions(self):
        """Return setup instructions for the Gmail tool"""
        return """
Gmail Tool Setup Instructions:

1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Go to "Credentials" and create an OAuth 2.0 Client ID
5. Download the credentials JSON file
6. Rename the downloaded file to 'credentials.json'
7. Place 'credentials.json' in the project root directory
8. The first time you use the tool, it will open a browser window for authentication
9. After authentication, a 'token.pickle' file will be created for future use

Note: The tool only requests permission to send emails, not read them.
"""
