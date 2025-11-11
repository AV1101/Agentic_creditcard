import random
import time
import smtplib
from email.mime.text import MIMEText
from db_operations import get_mobile_by_aadhaar
from typing import Dict
import time
import logging
import re
logger = logging.getLogger("OTP-Simulator")

# Store OTPs and expiry timestamps
otp_store = {}
aadhaar_otp_store = {}

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = ""  # <-- Add your email here
EMAIL_PASSWORD = ""  # Add your email password here


def generate_email_otp(email: str) -> dict:
    otp = str(random.randint(100000, 999999))
    otp_store[email] = {"otp": otp, "expiry": time.time() + 300}

    try:
        send_email_otp(email, otp)
        print(f"[SIMULATOR] OTP for {email}: {otp}")
        return {"success": True, "otp": otp}
    except Exception as e:
        print(f"Failed to send email OTP: {e}")
        return {"success": False, "error": str(e)}


def send_email_otp(email, otp):
    msg = MIMEText(f"""
The OTP to verify your email account for your Credit Card through Credentic: {otp}\n\n
Thank you for choosing Credentic AI for your Credit Card application.
This OTP is only valid for the next 5 minutes.\n\n
This is an automatically generated message, please do not reply to this email.\n\n
Regards,
Credentic
""")
    msg["Subject"] = "OTP Verification"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.set_debuglevel(1)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, email, msg.as_string())



def verify_email_otp(email: str, otp_input: str) -> dict:
    entry = otp_store.get(email)
    if not entry:
        return {"success": False, "error": "No OTP found for this email"}
    if time.time() > entry["expiry"]:
        return {"success": False, "error": "OTP expired"}
    if entry["otp"] == otp_input:
        return {"success": True}
    return {"success": False, "error": "Invalid OTP"}

def generate_aadhaar_otp(aadhaar: str) -> dict:
    otp = str(197653)  # static simulator OTP
    try:
        result = get_mobile_by_aadhaar(aadhaar)  # keep existing call
        logger.debug(f"[generate_aadhaar_otp] db result: {result} (type={type(result)})")

        # Normalize result -> mobile string
        if isinstance(result, dict):
            mobile = result.get("Mobile") or result.get("mobile")
        else:
            mobile = result

        # Final coercion to a digits-only string if possible
        if mobile is not None:
            mobile = str(mobile)
            # strip non-digits (optional)
            mobile_digits = re.sub(r'\D', '', mobile)
            if mobile_digits:
                mobile = mobile_digits

        if not mobile:
            logger.warning(f"[generate_aadhaar_otp] No mobile found for Aadhaar {aadhaar}: {result}")
            return {"success": False, "error": "No mobile linked to Aadhaar"}

        # store OTP
        aadhaar_otp_store[aadhaar] = {"otp": otp, "expiry": time.time() + 300}
        logger.info(f"[SIMULATOR] OTP for Aadhaar {aadhaar} (sent to mobile {mobile}): {otp}")

        # ALWAYS return mobile as a plain string
        return {"success": True, "otp": otp, "mobile": mobile}

    except Exception as e:
        logger.exception(f"Exception in generate_aadhaar_otp for Aadhaar {aadhaar}: {e}")
        return {"success": False, "error": str(e)}

def verify_aadhaar_otp(aadhaar: str, otp_input: str) -> dict:
    record = aadhaar_otp_store.get(aadhaar)
    if not record:
        return {"success": False, "error": "No OTP found for this Aadhaar"}
    if time.time() > record["expiry"]:
        return {"success": False, "error": "OTP expired"}
    if record["otp"] == otp_input:
        return {"success": True}
    return {"success": False, "error": "Invalid OTP"}


def send_email_confirmation(email):
    msg = MIMEText(f"""
Thank you for choosing Credentic AI for your Credit card application. Your application is currently being processed. \n\n 
Your application will now be handled by the Bank which issues the card you opted for.\n\n
This is an automatically generated message, please do not reply to this email.\n\n
Regards
Credentic""")
    msg["Subject"] = "Credit Card Application Confirmation"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.set_debuglevel(1)  
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())
        print("Email confirmation sent successfully")
        
    except Exception as e:
        print("Failed to send email confirmation:", e)

def send_email_aa(email, url):
    if isinstance(email, str):
        email = [email]
    email_str = ", ".join(email)

    msg = MIMEText(f"""
Thank you for choosing Pennfinn bike loan. Please accept the consent for Account Aggregator here:\n {url} 
Declining the URL will prevent loan booking. Kindly accept to proceed.\n
Regards
PennFinn""")

    msg["Subject"] = "Account Aggregator consent"
    msg["From"] = EMAIL_USER
    msg["To"] = email_str  

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.set_debuglevel(1) 
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())  
        print("Consent email sent successfully")
        print(f"[SIMULATOR] Sent AA to {email}:{url}")
    except Exception as e:
        print("Failed to send consent page url to the given email:", e)

