# Python 3.7
# File name: 
# Authors: Aaron Watt
# Date: 2021-07-09
"""Sending text messages over Aaron's gmail account."""
# Standard library imports
import smtplib
import ssl

# Third-party imports

# Local application imports

# GLOBALS ----------------------------


# FUNCTIONS --------------------------
def send_text(subject, body):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "kratzer.canby@gmail.com"  # Enter your address
    receiver_email = '5033279232@msg.fi.google.com'  # Enter receiver address
    password = 'ktziyuaefqmbhxgh'
    message = f"""
    Subject: {subject}
    
    {body}
    """

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


# MAIN -------------------------------
if __name__ == "__main__":
    send_text()

# REFERENCES -------------------------
"""

"""
