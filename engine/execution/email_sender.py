#!/usr/bin/env python3
"""
Email Sender - Send individual emails via Brevo (Sendinblue)
Includes tracking pixel insertion and link click tracking.

Input: CLI arguments with email details
Output: Success/failure status, logs to database
"""

import argparse
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()


def get_brevo_api_key() -> str:
    """Get Brevo API key from environment."""
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("[ERROR] BREVO_API_KEY not found in environment variables")
        sys.exit(1)
    return api_key


def generate_tracking_id() -> str:
    """Generate a unique tracking ID for this email."""
    return str(uuid.uuid4())


def insert_tracking_pixel(html_content: str, tracking_id: str, tracking_domain: str) -> str:
    """
    Insert a 1x1 transparent tracking pixel at the end of email body.
    
    This allows us to track when the recipient opens the email.
    """
    pixel_url = f"{tracking_domain}/webhooks/email/open?tracking_id={tracking_id}"
    tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
    
    # Insert before closing </body> tag, or at the end if no body tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
    else:
        html_content += tracking_pixel
    
    return html_content


def wrap_links_with_tracking(html_content: str, tracking_id: str, tracking_domain: str) -> str:
    """
    Wrap all links in the email with click tracking redirects.
    
    Original: <a href="https://example.com">Click here</a>
    Wrapped: <a href="https://api.yourdomain.com/webhooks/email/click/TRACKING_ID?url=https%3A%2F%2Fexample.com">Click here</a>
    """
    # Simple regex to find href attributes
    def replace_href(match):
        original_url = match.group(1)
        
        # Skip tracking for unsubscribe/tracking links
        if 'unsubscribe' in original_url.lower() or 'mailto:' in original_url.lower():
            return match.group(0)
        
        # Encode the original URL
        encoded_url = quote(original_url, safe='')
        
        # Create tracking URL
        tracking_url = f"{tracking_domain}/webhooks/email/click/{tracking_id}?url={encoded_url}"
        
        return f'href="{tracking_url}"'
    
    # Replace all href="..." with tracked versions
    tracked_content = re.sub(r'href="([^"]+)"', replace_href, html_content)
    
    return tracked_content


def convert_template_to_html(template_text: str) -> str:
    """
    Convert plain text email template to basic HTML.
    
    Preserves line breaks and basic formatting.
    """
    # Escape HTML characters
    html = template_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convert newlines to <br>
    html = html.replace('\\n', '<br>')
    
    # Wrap in basic HTML structure
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
        {html}
    </div>
</body>
</html>
"""
    return html_template


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    content: str,
    from_email: str,
    from_name: str,
    tracking_id: str,
    tracking_domain: str
) -> dict:
    """
    Send an email via Brevo (Sendinblue) API with tracking.
    
    Returns a dict with success status and any error messages.
    """
    try:
        # Convert plain text template to HTML
        html_content = convert_template_to_html(content)
        
        # Add tracking pixel
        html_content = insert_tracking_pixel(html_content, tracking_id, tracking_domain)
        
        # Wrap links with click tracking
        html_content = wrap_links_with_tracking(html_content, tracking_id, tracking_domain)
        
        # Get API key
        api_key = get_brevo_api_key()
        
        # Prepare Brevo API request
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {
                "name": from_name,
                "email": from_email
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }
        
        # Send via Brevo
        response = requests.post(url, json=payload, headers=headers)
        
        # Check response
        if response.status_code in [200, 201, 202]:
            print(f"[SUCCESS] Email sent to {to_email}")
            return {
                "success": True,
                "status_code": response.status_code,
                "error": None
            }
        else:
            error_msg = response.text
            print(f"[ERROR] Brevo API error: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return {
            "success": False,
            "status_code": None,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Send email via Brevo with tracking")
    parser.add_argument("--to-email", required=True, help="Recipient email address")
    parser.add_argument("--to-name", required=True, help="Recipient name")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--content", required=True, help="Email body content")
    parser.add_argument("--tracking-id", required=True, help="Unique tracking ID")
    parser.add_argument("--campaign-id", help="Campaign ID (for logging)")
    
    args = parser.parse_args()
    
    # Get configuration from environment
    from_email = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
    from_name = os.getenv("FROM_NAME", "Your Company")
    tracking_domain = os.getenv("TRACKING_DOMAIN", "http://localhost:8000")
    
    # Send the email
    result = send_email(
        to_email=args.to_email,
        to_name=args.to_name,
        subject=args.subject,
        content=args.content,
        from_email=from_email,
        from_name=from_name,
        tracking_id=args.tracking_id,
        tracking_domain=tracking_domain
    )
    
    # Exit with appropriate code
    if result["success"]:
        print(f"[EMAIL SENDER] Successfully sent email to {args.to_email}")
        sys.exit(0)
    else:
        print(f"[EMAIL SENDER FAILED] Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()



def generate_tracking_id() -> str:
    """Generate a unique tracking ID for this email."""
    return str(uuid.uuid4())


def insert_tracking_pixel(html_content: str, tracking_id: str, tracking_domain: str) -> str:
    """
    Insert a 1x1 transparent tracking pixel at the end of email body.
    
    This allows us to track when the recipient opens the email.
    """
    pixel_url = f"{tracking_domain}/webhooks/email/open?tracking_id={tracking_id}"
    tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
    
    # Insert before closing </body> tag, or at the end if no body tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
    else:
        html_content += tracking_pixel
    
    return html_content


def wrap_links_with_tracking(html_content: str, tracking_id: str, tracking_domain: str) -> str:
    """
    Wrap all links in the email with click tracking redirects.
    
    Original: <a href="https://example.com">Click here</a>
    Wrapped: <a href="https://api.yourdomain.com/webhooks/email/click/TRACKING_ID?url=https%3A%2F%2Fexample.com">Click here</a>
    """
    # Simple regex to find href attributes
    # This is a basic implementation - production should use proper HTML parsing
    def replace_href(match):
        original_url = match.group(1)
        
        # Skip tracking for unsubscribe/tracking links
        if 'unsubscribe' in original_url.lower() or 'mailto:' in original_url.lower():
            return match.group(0)
        
        # Encode the original URL
        encoded_url = quote(original_url, safe='')
        
        # Create tracking URL
        tracking_url = f"{tracking_domain}/webhooks/email/click/{tracking_id}?url={encoded_url}"
        
        return f'href="{tracking_url}"'
    
    # Replace all href="..." with tracked versions
    tracked_content = re.sub(r'href="([^"]+)"', replace_href, html_content)
    
    return tracked_content


def convert_template_to_html(template_text: str) -> str:
    """
    Convert plain text email template to basic HTML.
    
    Preserves line breaks and basic formatting.
    """
    # Escape HTML characters
    html = template_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convert newlines to <br>
    html = html.replace('\\n', '<br>')
    
    # Wrap in basic HTML structure
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
        {html}
    </div>
</body>
</html>
"""
    return html_template


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    content: str,
    from_email: str,
    from_name: str,
    tracking_id: str,
    tracking_domain: str
) -> dict:
    """
    Send an email via SendGrid with tracking.
    
    Returns a dict with success status and any error messages.
    """
    try:
        # Convert plain text template to HTML
        html_content = convert_template_to_html(content)
        
        # Add tracking pixel
        html_content = insert_tracking_pixel(html_content, tracking_id, tracking_domain)
        
        # Wrap links with click tracking
        html_content = wrap_links_with_tracking(html_content, tracking_id, tracking_domain)
        
        # Create the email message
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(to_email, to_name),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        # Send via SendGrid
        sg = get_sendgrid_client()
        response = sg.send(message)
        
        # Check response
        if response.status_code in [200, 201, 202]:
            print(f"[SUCCESS] Email sent to {to_email}")
            return {
                "success": True,
                "status_code": response.status_code,
                "error": None
            }
        else:
            print(f"[WARNING] Unexpected status code: {response.status_code}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"Unexpected status code: {response.status_code}"
            }
            
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return {
            "success": False,
            "status_code": None,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Send email via SendGrid with tracking")
    parser.add_argument("--to-email", required=True, help="Recipient email address")
    parser.add_argument("--to-name", required=True, help="Recipient name")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--content", required=True, help="Email body content")
    parser.add_argument("--tracking-id", required=True, help="Unique tracking ID")
    parser.add_argument("--campaign-id", help="Campaign ID (for logging)")
    
    args = parser.parse_args()
    
    # Get configuration from environment
    from_email = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
    from_name = os.getenv("FROM_NAME", "Your Company")
    tracking_domain = os.getenv("TRACKING_DOMAIN", "http://localhost:8000")
    
    # Send the email
    result = send_email(
        to_email=args.to_email,
        to_name=args.to_name,
        subject=args.subject,
        content=args.content,
        from_email=from_email,
        from_name=from_name,
        tracking_id=args.tracking_id,
        tracking_domain=tracking_domain
    )
    
    # Exit with appropriate code
    if result["success"]:
        print(f"[EMAIL SENDER] Successfully sent email to {args.to_email}")
        sys.exit(0)
    else:
        print(f"[EMAIL SENDER FAILED] Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
