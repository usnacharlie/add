# membership_notifications.py - Notification Service for ADD Zambia Membership System
"""
Handles email and SMS notifications for membership events
"""

import os
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service for membership system"""

    def __init__(self):
        # Email configuration - Titan Email
        self.mail_server = os.getenv('MAIL_SERVER', 'smtp.titan.email')
        self.mail_port = int(os.getenv('MAIL_PORT', '587'))
        self.mail_username = os.getenv('MAIL_USERNAME', 'no_reply@ontech.co.zm')
        self.mail_password = os.getenv('MAIL_PASSWORD', '')
        self.mail_from = os.getenv('MAIL_DEFAULT_SENDER', 'ADD Zambia <no_reply@ontech.co.zm>')

        # SMS configuration - CloudServiceZM
        self.sms_enabled = os.getenv('ENABLE_SMS_ALERTS', 'True').lower() == 'true'
        self.sms_api_url = os.getenv('CLOUDSERVICEZM_API_URL', 'https://www.cloudservicezm.com/smsservice/httpapi')
        self.sms_username = os.getenv('CLOUDSERVICEZM_USERNAME', 'Chileshe')
        self.sms_password = os.getenv('CLOUDSERVICEZM_PASSWORD', 'Chileshe1')
        self.sms_shortcode = os.getenv('CLOUDSERVICEZM_SHORTCODE', '388')
        self.sms_sender_id = os.getenv('CLOUDSERVICEZM_SENDER_ID', '388')
        self.sms_api_key = os.getenv('CLOUDSERVICEZM_API_KEY', 'use_preshared')

        logger.info(f"Notification service initialized - Email: {self.mail_server}, SMS: {'Enabled' if self.sms_enabled else 'Disabled'}")

    # ==========================================================================
    # SMS METHODS
    # ==========================================================================

    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via CloudServiceZM"""
        try:
            if not self.sms_enabled:
                logger.warning("SMS service disabled - skipping SMS")
                return False

            # Clean phone number (remove spaces, dashes, etc.)
            clean_phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
            if clean_phone.startswith('0'):
                clean_phone = '260' + clean_phone[1:]
            elif clean_phone.startswith('+260'):
                clean_phone = clean_phone[1:]
            elif not clean_phone.startswith('260'):
                clean_phone = '260' + clean_phone

            # Prepare API parameters
            params = {
                'username': self.sms_username,
                'password': self.sms_password,
                'msg': message[:160],  # Limit to 160 characters
                'shortcode': self.sms_shortcode,
                'sender_id': self.sms_sender_id,
                'phone': clean_phone,
                'api_key': self.sms_api_key
            }

            logger.info(f"📱 Sending SMS to {clean_phone}")

            response = requests.get(self.sms_api_url, params=params, timeout=30)

            if response.status_code == 200 and 'success' in response.text.lower():
                logger.info(f"✅ SMS sent to {clean_phone}: {response.text}")
                return True
            else:
                logger.error(f"❌ SMS API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
            return False

    def send_welcome_sms(self, member):
        """Send welcome SMS to new member"""
        message = f"Welcome to ADD Zambia! Your membership number is {member.membership_number}. Complete payment of K25 to activate. Visit addzambia.com/member"

        if member.phone_number:
            return self.send_sms(member.phone_number, message)
        return False

    def send_payment_confirmation_sms(self, member, payment):
        """Send payment confirmation SMS"""
        message = f"Payment confirmed! Receipt: {payment.receipt_number}. Amount: K{payment.amount}. Your ADD membership is now active. Thank you!"

        if member.phone_number:
            return self.send_sms(member.phone_number, message)
        return False

    def send_payment_reminder_sms(self, member):
        """Send payment reminder SMS"""
        message = f"Dear {member.first_name}, your ADD membership payment of K25 is pending. Pay via *303# (MTN). Membership: {member.membership_number}"

        if member.phone_number:
            return self.send_sms(member.phone_number, message)
        return False

    def send_renewal_reminder_sms(self, member, days_remaining):
        """Send renewal reminder SMS"""
        message = f"Dear {member.first_name}, your ADD membership expires in {days_remaining} days. Renew now to continue enjoying member benefits. K25 via *303#"

        if member.phone_number:
            return self.send_sms(member.phone_number, message)
        return False

    # ==========================================================================
    # EMAIL METHODS
    # ==========================================================================

    def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via Titan Email SMTP"""
        try:
            if not self.mail_password:
                logger.warning("Email password not configured - skipping email")
                return False

            msg = MIMEMultipart('alternative')
            msg['From'] = self.mail_from
            msg['To'] = to_email
            msg['Subject'] = subject

            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.mail_server, self.mail_port) as server:
                server.starttls()
                server.login(self.mail_username, self.mail_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False

    def send_welcome_email(self, member):
        """Send welcome email to new member"""
        subject = f"Welcome to ADD Zambia - {member.first_name}!"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #0066CC; color: white; padding: 30px 20px; text-align: center;">
                    <img src="https://addzambia.com/static/img/logoadd.jpeg" alt="ADD Logo" style="width: 80px; height: 80px; margin-bottom: 15px; border-radius: 10px;">
                    <h1 style="margin: 0;">Welcome to ADD Zambia!</h1>
                </div>

                <div style="padding: 30px 20px;">
                    <h2 style="color: #0066CC;">Hello {member.first_name} {member.last_name},</h2>

                    <p style="font-size: 16px; line-height: 1.6;">
                        Thank you for joining the Alliance for Democracy and Development (ADD).
                        Your membership has been successfully registered!
                    </p>

                    <div style="background-color: #e7f3ff; border-left: 5px solid #0066CC; padding: 20px; margin: 25px 0;">
                        <h3 style="margin-top: 0; color: #0066CC;">Your Membership Details</h3>
                        <p style="margin: 5px 0;"><strong>Membership Number:</strong> {member.membership_number}</p>
                        <p style="margin: 5px 0;"><strong>Name:</strong> {member.first_name} {member.last_name}</p>
                        <p style="margin: 5px 0;"><strong>Constituency:</strong> {member.constituency}</p>
                        <p style="margin: 5px 0;"><strong>Registration Date:</strong> {member.created_at.strftime('%Y-%m-%d') if member.created_at else 'N/A'}</p>
                    </div>

                    <h3 style="color: #0066CC;">Next Steps:</h3>
                    <ol style="line-height: 1.8;">
                        <li>Complete your membership payment of K25.00</li>
                        <li>Access your member portal at <a href="https://addzambia.com/member">addzambia.com/member</a></li>
                        <li>Download your membership card</li>
                        <li>Participate in party activities and events</li>
                    </ol>

                    <div style="background-color: #fff3cd; border-left: 5px solid #FF6600; padding: 15px; margin: 25px 0;">
                        <h4 style="margin-top: 0; color: #856404;">📱 Payment Options</h4>
                        <p style="margin-bottom: 0;">
                            Pay via Mobile Money: *303# (MTN) or visit our website for other payment methods.
                        </p>
                    </div>

                    <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                        If you have any questions, please contact us or visit your nearest ADD office.
                    </p>
                </div>

                <div style="background-color: #0066CC; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">ADD Zambia - Building a Better Tomorrow</p>
                    <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">
                        This is an automated message from ADD Zambia Membership System
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        if member.email:
            return self.send_email(member.email, subject, html_body)
        return False

    def send_payment_confirmation_email(self, member, payment):
        """Send payment confirmation email"""
        subject = f"Payment Confirmed - Receipt {payment.receipt_number}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #28a745; color: white; padding: 30px 20px; text-align: center;">
                    <img src="https://addzambia.com/static/img/logoadd.jpeg" alt="ADD Logo" style="width: 80px; height: 80px; margin-bottom: 15px; border-radius: 10px;">
                    <h1 style="margin: 0;">✅ Payment Confirmed</h1>
                </div>

                <div style="padding: 30px 20px;">
                    <h2 style="color: #28a745;">Dear {member.first_name},</h2>

                    <p style="font-size: 16px; line-height: 1.6;">
                        Your membership payment has been successfully received and confirmed!
                    </p>

                    <div style="background-color: #d4edda; border-left: 5px solid #28a745; padding: 20px; margin: 25px 0;">
                        <h3 style="margin-top: 0; color: #155724;">Payment Receipt</h3>
                        <p style="margin: 5px 0;"><strong>Receipt Number:</strong> {payment.receipt_number}</p>
                        <p style="margin: 5px 0;"><strong>Amount:</strong> K{payment.amount}</p>
                        <p style="margin: 5px 0;"><strong>Payment Method:</strong> {payment.payment_method.upper()}</p>
                        <p style="margin: 5px 0;"><strong>Payment Date:</strong> {payment.payment_date.strftime('%Y-%m-%d %H:%M') if payment.payment_date else 'N/A'}</p>
                        <p style="margin: 5px 0;"><strong>Payment Year:</strong> {payment.payment_year}</p>
                        <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">COMPLETED</span></p>
                    </div>

                    <h3 style="color: #0066CC;">Your Membership is Now Active!</h3>
                    <p>You can now:</p>
                    <ul style="line-height: 1.8;">
                        <li>Access your digital membership card</li>
                        <li>Participate in party events and activities</li>
                        <li>Vote in party elections</li>
                        <li>Refer friends and family to join ADD</li>
                    </ul>

                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://addzambia.com/member/membership_card"
                           style="background-color: #0066CC; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Your Membership Card
                        </a>
                    </p>
                </div>

                <div style="background-color: #0066CC; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">ADD Zambia - Thank you for your support!</p>
                </div>
            </div>
        </body>
        </html>
        """

        if member.email:
            return self.send_email(member.email, subject, html_body)
        return False

    # ==========================================================================
    # COMBINED NOTIFICATIONS
    # ==========================================================================

    def notify_new_member(self, member):
        """Send welcome notification via email and SMS"""
        email_sent = False
        if member.email:
            email_sent = self.send_welcome_email(member)

        sms_sent = self.send_welcome_sms(member)

        logger.info(f"New member notification for {member.membership_number} - Email: {email_sent}, SMS: {sms_sent}")
        return email_sent or sms_sent

    def notify_payment_confirmed(self, member, payment):
        """Send payment confirmation via email and SMS"""
        email_sent = False
        if member.email:
            email_sent = self.send_payment_confirmation_email(member, payment)

        sms_sent = self.send_payment_confirmation_sms(member, payment)

        logger.info(f"Payment confirmation for {member.membership_number} - Email: {email_sent}, SMS: {sms_sent}")
        return email_sent or sms_sent


# Create global notification service instance
notification_service = NotificationService()
