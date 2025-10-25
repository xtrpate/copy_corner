import mysql.connector
from tkinter import messagebox, Canvas
import os # <-- Added
import smtplib # <-- Added
from email.mime.text import MIMEText # <-- Added
from email.mime.multipart import MIMEMultipart # <-- Added
from dotenv import load_dotenv # <-- Added

load_dotenv() # Load environment variables once when utils is imported

# --- Database Connection ---
def get_db_connection():
    """Establishes connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"), # Use env var or default
            user=os.getenv("DB_USER", "root"),       # Use env var or default
            password=os.getenv("DB_PASS", ""),       # Use env var or default
            database=os.getenv("DB_NAME", "copy_corner_db") # Use env var or default
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
        return None

# --- Rounded Rectangle ---
def round_rectangle(canvas: Canvas, x1: float, y1: float, x2: float, y2: float, r: int = 15, **kwargs):
    """Draws a rounded rectangle on the canvas."""
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        x1 + r, y1 # Explicitly close path point for some Tk versions
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# --- Send Verification Email --- # <-- NEW SECTION ADDED
def send_verification_email(user_email, otp_code, email_subject="Email Verification", context="verify"):
    """Sends the OTP code to the user's email."""

    sender_email = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")

    if not sender_email or not app_password:
        messagebox.showerror("Configuration Error",
                             "Email credentials not found in .env file (EMAIL_USER, EMAIL_PASS).")
        return False

    # Customize message slightly based on context
    if context == "reset":
        intro_line = "You requested to reset your password. Please use the following code to verify your email address:"
        note_line = "If you did not request this, please ignore this email."
    else: # Default verification message
        intro_line = "Your account is nearly set up. Please use this code to verify your email address."
        note_line = ""

    html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="background-color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="color: #222;">{email_subject}</h2>
                </div>
                <div style="padding: 30px; color: #333;">
                    <p>Hello,</p>
                    <p>{intro_line}</p>
                    <div style="background-color: #f1f1f1; border-radius: 5px; text-align: center; font-size: 28px;
                                letter-spacing: 5px; padding: 15px 0; margin: 25px 0; font-weight: bold; color: #333;">
                        {otp_code}
                    </div>
                    <p style="font-size: 14px; text-align: center; color: #555;">
                        <b>{note_line} Code will expire in 30 minutes.</b>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = email_subject
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, user_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        messagebox.showerror("Email Error", f"Could not send email.\n\nError: {e}")
        return False