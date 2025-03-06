import os
from dotenv import load_dotenv

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool


load_dotenv()
smtp_server = "smtp.gmail.com"
smtp_port = 587

sender_email = os.getenv('EMAIL_ADDRESS')
smtp_username = os.getenv('EMAIL_ADDRESS')
smtp_password = os.getenv('APP_PASSWORD')

@tool
def send_email(subject, body, recipient_email):
    '''
    Sends email to the given recipient email address.
    '''
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

