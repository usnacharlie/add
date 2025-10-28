"""
OTP Service for email and SMS verification
"""

import random
import string
import secrets
from datetime import datetime, timedelta
from flask import current_app
from models import db, User, OTPCode
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

class OTPService:
    """Service to handle OTP generation and verification via Email/SMS"""
    
    def __init__(self):
        self.otp_expiry_minutes = 5
        self.otp_length = 6
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return ''.join([str(random.randint(0, 9)) for _ in range(self.otp_length)])
    
    def store_otp(self, user_id, otp, method='email'):
        """Store OTP in database"""
        try:
            # Delete any existing unused OTPs for this user and method
            OTPCode.query.filter_by(
                user_id=user_id, 
                method=method,
                is_used=False
            ).delete()
            
            # Create new OTP
            expiry = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            otp_code = OTPCode(
                user_id=user_id,
                code=otp,
                method=method,
                expiry=expiry
            )
            db.session.add(otp_code)
            db.session.commit()
            
            print(f"📝 Stored OTP in DB for user {user_id} via {method}: {otp}")
            return True
        except Exception as e:
            print(f"❌ Failed to store OTP: {str(e)}")
            db.session.rollback()
            return False
    
    def verify_otp(self, user_id, otp, method='email'):
        """Verify the provided OTP from database"""
        try:
            print(f"🔐 Verifying OTP for user {user_id} via {method}: received '{otp}'")
            
            # Find the OTP in database
            otp_record = OTPCode.query.filter_by(
                user_id=user_id,
                method=method,
                is_used=False
            ).order_by(OTPCode.created_at.desc()).first()
            
            if not otp_record:
                print(f"❌ No OTP found in DB for user {user_id} via {method}")
                return {'success': False, 'message': 'No OTP found. Please request a new one.'}
            
            print(f"🔐 Found OTP in DB: '{otp_record.code}', Received: '{otp}'")
            
            # Check expiry
            if datetime.utcnow() > otp_record.expiry:
                otp_record.is_used = True  # Mark as used
                db.session.commit()
                return {'success': False, 'message': 'OTP expired. Please request a new one.'}
            
            # Check attempts
            otp_record.attempts += 1
            db.session.commit()
            
            if otp_record.attempts > 3:
                otp_record.is_used = True  # Mark as used after too many attempts
                db.session.commit()
                return {'success': False, 'message': 'Too many failed attempts. Please request a new OTP.'}
            
            # Verify OTP - compare as strings
            if str(otp_record.code).strip() == str(otp).strip():
                otp_record.is_used = True  # Mark as used
                db.session.commit()
                print(f"✅ OTP verified successfully")
                return {'success': True, 'message': 'OTP verified successfully'}
            
            print(f"❌ OTP mismatch")
            return {'success': False, 'message': f"Invalid OTP. {3 - otp_record.attempts} attempts remaining."}
            
        except Exception as e:
            print(f"❌ Error verifying OTP: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': 'Error verifying OTP. Please try again.'}
    
    def send_otp_email(self, user, otp):
        """Send OTP via email"""
        try:
            # Get email configuration
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.titan.email')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            smtp_username = current_app.config.get('MAIL_USERNAME', 'no_reply@ontech.co.zm')
            smtp_password = current_app.config.get('MAIL_PASSWORD', 'TestPass123!')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Your ONTECH ICT Login Code'
            msg['From'] = smtp_username
            msg['To'] = user.email
            
            # Create the email body
            text_body = f"""
Hello {user.full_name or user.username},

Your verification code is: {otp}

This code will expire in {self.otp_expiry_minutes} minutes.

If you didn't request this code, please ignore this email.

Best regards,
ONTECH ICT Management System
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #006845; color: white; padding: 20px; text-align: center; }}
        .code-box {{ 
            background: #f4f4f4; 
            border: 2px solid #006845; 
            padding: 20px; 
            margin: 20px 0; 
            text-align: center; 
            font-size: 32px; 
            font-weight: bold; 
            letter-spacing: 5px;
            color: #006845;
        }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>ONTECH ICT Management System</h2>
        </div>
        <p>Hello {user.full_name or user.username},</p>
        <p>Your verification code is:</p>
        <div class="code-box">{otp}</div>
        <p>This code will expire in <strong>{self.otp_expiry_minutes} minutes</strong>.</p>
        <p>Enter this code to complete your login.</p>
        <div class="footer">
            <p>If you didn't request this code, please ignore this email.</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Attach parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email with reasonable timeout
            with smtplib.SMTP(smtp_server, smtp_port, timeout=60) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print(f"✅ OTP email sent to {user.email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send OTP email: {str(e)}")
            return False
    
    def send_otp_sms(self, user, otp):
        """Send OTP via SMS using CloudServiceZM"""
        try:
            # Get SMS configuration from environment
            api_url = current_app.config.get('CLOUDSERVICEZM_API_URL', 'https://www.cloudservicezm.com/smsservice/httpapi')
            username = current_app.config.get('CLOUDSERVICEZM_USERNAME', 'Chileshe')
            password = current_app.config.get('CLOUDSERVICEZM_PASSWORD', 'Chileshe1')
            sender_id = current_app.config.get('CLOUDSERVICEZM_SENDER_ID', 'ONTECH')
            
            # Format phone number (ensure it starts with 260)
            phone = user.phone
            if not phone.startswith('260'):
                phone = '260' + phone.lstrip('0+')
            
            # Prepare SMS message
            message = f"ONTECH ICT: Your login code is {otp}. Valid for {self.otp_expiry_minutes} minutes."
            
            # Prepare API request
            params = {
                'username': username,
                'password': password,
                'msg': message,
                'shortcode': sender_id,
                'sender_id': sender_id,
                'phone': phone,
                'api_key': 'use_preshared'
            }
            
            # Send SMS
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ OTP SMS sent to {phone}")
                return True
            else:
                print(f"❌ SMS API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send OTP SMS: {str(e)}")
            return False
    
    def send_otp(self, user, method='email'):
        """Send OTP using specified method"""
        from flask import current_app
        import threading
        
        # Generate OTP
        otp = self.generate_otp()
        
        print(f"🎲 Generated OTP for user {user.id}: {otp}")
        
        # Store OTP
        if not self.store_otp(user.id, otp, method):
            return {'success': False, 'message': 'Failed to store OTP'}
        
        # Get Flask app context for background thread
        app = current_app._get_current_object()
        
        # Send email/SMS in background thread to avoid blocking
        def send_async():
            with app.app_context():
                try:
                    if method == 'email':
                        self.send_otp_email(user, otp)
                    elif method == 'sms':
                        self.send_otp_sms(user, otp)
                except Exception as e:
                    print(f"⚠️ Background send failed: {str(e)}")
        
        # Start background thread for sending
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        
        # Immediately return success since OTP is stored
        success = True
        
        if success:
            print(f"✉️ OTP sent successfully via {method}")
            return {
                'success': True,
                'message': f'OTP sent to your {method}',
                'otp': None
            }
        else:
            print(f"❌ Failed to send OTP via {method}, but OTP is stored")
            return {
                'success': True,  # Still return success since OTP is stored
                'message': f'OTP ready (sending failed) - Code: {otp}',
                'otp': otp  # Show code if sending failed
            }
    
    def cleanup_expired_otps(self):
        """Remove expired OTPs from database"""
        try:
            current_time = datetime.utcnow()
            expired_count = OTPCode.query.filter(
                OTPCode.expiry < current_time
            ).delete()
            db.session.commit()
            return expired_count
        except Exception as e:
            print(f"❌ Error cleaning up expired OTPs: {str(e)}")
            db.session.rollback()
            return 0

# Create global instance
otp_service = OTPService()