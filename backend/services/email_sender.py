import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def send_email(subject: str, html_body: str, config: dict) -> dict:
    gmail_address = config["gmail_address"]
    gmail_app_password = config["gmail_app_password"]
    recipient_email = config["recipient_email"]

    msg = MIMEMultipart("alternative")
    msg["From"] = gmail_address
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, recipient_email, msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
