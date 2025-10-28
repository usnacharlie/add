# services/two_factor_service.py
"""
Two-Factor Authentication Service for ONTECH ICT Management System
"""

import random
import string
import secrets
from datetime import datetime, timedelta
from flask import current_app, request
import pyotp
from models import db, TwoFactorMethod, TwoFactorBackupCode, TwoFactorSession, TwoFactorAuditLog
from services.sms_service import SMSService
from services.notification_service import NotificationService

class TwoFactorService:
    """Service to handle all 2FA operations"""
    
    def __init__(self):
        self.sms_service = SMSService()
        self.notification_service = NotificationService()
    
    def enable_2fa_for_user(self, user, method_type='email', contact_info=None):
        """Enable 2FA for a user with specified method"""
        try:
            # Check if method already exists
            existing = TwoFactorMethod.query.filter_by(
                user_id=user.id,
                method_type=method_type
            ).first()
            
            if existing and existing.is_verified:
                return {'success': False, 'message': f'{method_type.upper()} 2FA already enabled'}
            
            # Create or update 2FA method
            if existing:
                twofa_method = existing
            else:
                twofa_method = TwoFactorMethod(
                    user_id=user.id,
                    method_type=method_type
                )
            
            # Set contact information
            if method_type == 'sms':
                if not contact_info or 'phone' not in contact_info:
                    return {'success': False, 'message': 'Phone number required for SMS 2FA'}
                twofa_method.phone_number = self._format_phone_number(contact_info['phone'])
            elif method_type == 'email':
                twofa_method.email_address = contact_info.get('email', user.email)
            elif method_type == 'totp':
                # Generate TOTP secret
                twofa_method.totp_secret = pyotp.random_base32()
            
            # Generate and send verification code for SMS/Email
            if method_type in ['sms', 'email']:
                code = twofa_method.generate_verification_code()
                
                if method_type == 'sms':
                    self._send_sms_code(twofa_method.phone_number, code, user)
                else:
                    self._send_email_code(twofa_method.email_address, code, user)
            
            # Set as primary if first method
            if not TwoFactorMethod.query.filter_by(user_id=user.id, is_verified=True).first():
                twofa_method.is_primary = True
            
            db.session.add(twofa_method)
            db.session.commit()
            
            # Log the event
            TwoFactorAuditLog.log_event(
                user_id=user.id,
                event_type='enable_initiated',
                method_type=method_type,
                request_info=self._get_request_info()
            )
            
            return {
                'success': True,
                'message': f'Verification code sent via {method_type}',
                'method_id': twofa_method.id,
                'totp_secret': twofa_method.totp_secret if method_type == 'totp' else None,
                'totp_qr': self._generate_totp_qr(user, twofa_method.totp_secret) if method_type == 'totp' else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error enabling 2FA: {str(e)}")
            return {'success': False, 'message': 'Failed to enable 2FA'}
    
    def verify_2fa_code(self, user, code, method_id=None):
        """Verify a 2FA code"""
        try:
            # Get the 2FA method
            if method_id:
                method = TwoFactorMethod.query.get(method_id)
            else:
                # Get primary method
                method = TwoFactorMethod.query.filter_by(
                    user_id=user.id,
                    is_primary=True
                ).first()
            
            if not method:
                return {'success': False, 'message': 'No 2FA method found'}
            
            # Verify based on method type
            if method.method_type == 'totp':
                totp = pyotp.TOTP(method.totp_secret)
                if totp.verify(code, valid_window=1):
                    success = True
                else:
                    success = False
            else:
                # SMS or Email verification
                success = method.verify_code(code)
            
            if success:
                method.last_used = datetime.utcnow()
                
                # Update user's 2FA status
                if not user.two_factor_enabled:
                    user.two_factor_enabled = True
                    user.two_factor_enabled_at = datetime.utcnow()
                    
                    # Generate backup codes on first enable
                    backup_codes = TwoFactorBackupCode.generate_backup_codes(user.id)
                    
                db.session.commit()
                
                # Create trusted session
                session = TwoFactorSession.create_session(
                    user_id=user.id,
                    device_info=self._get_device_info()
                )
                db.session.commit()
                
                # Log success
                TwoFactorAuditLog.log_event(
                    user_id=user.id,
                    event_type='verified',
                    method_type=method.method_type,
                    request_info=self._get_request_info()
                )
                
                result = {
                    'success': True,
                    'message': '2FA verification successful',
                    'session_token': session.session_token
                }
                
                if backup_codes:
                    result['backup_codes'] = [bc.code for bc in backup_codes]
                
                return result
            else:
                # Log failure
                TwoFactorAuditLog.log_event(
                    user_id=user.id,
                    event_type='failed',
                    status='failure',
                    method_type=method.method_type,
                    request_info=self._get_request_info()
                )
                
                return {'success': False, 'message': 'Invalid verification code'}
                
        except Exception as e:
            current_app.logger.error(f"Error verifying 2FA: {str(e)}")
            return {'success': False, 'message': 'Verification failed'}
    
    def send_2fa_code(self, user, method_type=None):
        """Send a new 2FA code to user"""
        try:
            # Get the method
            if method_type:
                method = TwoFactorMethod.query.filter_by(
                    user_id=user.id,
                    method_type=method_type,
                    is_verified=True
                ).first()
            else:
                method = TwoFactorMethod.query.filter_by(
                    user_id=user.id,
                    is_primary=True,
                    is_verified=True
                ).first()
            
            if not method:
                return {'success': False, 'message': '2FA not enabled for this method'}
            
            if method.method_type == 'totp':
                return {'success': False, 'message': 'TOTP does not require sending codes'}
            
            # Generate and send code
            code = method.generate_verification_code()
            
            if method.method_type == 'sms':
                self._send_sms_code(method.phone_number, code, user)
                masked_phone = self._mask_phone(method.phone_number)
                message = f'Verification code sent to {masked_phone}'
            else:  # email
                self._send_email_code(method.email_address, code, user)
                masked_email = self._mask_email(method.email_address)
                message = f'Verification code sent to {masked_email}'
            
            db.session.commit()
            
            return {
                'success': True,
                'message': message,
                'method_type': method.method_type
            }
            
        except Exception as e:
            current_app.logger.error(f"Error sending 2FA code: {str(e)}")
            return {'success': False, 'message': 'Failed to send verification code'}
    
    def verify_backup_code(self, user, code):
        """Verify a backup code"""
        try:
            backup = TwoFactorBackupCode.query.filter_by(
                user_id=user.id,
                code=code,
                is_used=False
            ).first()
            
            if backup:
                backup.is_used = True
                backup.used_at = datetime.utcnow()
                db.session.commit()
                
                # Create session
                session = TwoFactorSession.create_session(
                    user_id=user.id,
                    device_info=self._get_device_info()
                )
                db.session.commit()
                
                # Log event
                TwoFactorAuditLog.log_event(
                    user_id=user.id,
                    event_type='backup_used',
                    details=f'Backup code used',
                    request_info=self._get_request_info()
                )
                
                # Check remaining backup codes
                remaining = TwoFactorBackupCode.query.filter_by(
                    user_id=user.id,
                    is_used=False
                ).count()
                
                return {
                    'success': True,
                    'message': 'Backup code verified',
                    'session_token': session.session_token,
                    'remaining_codes': remaining
                }
            else:
                TwoFactorAuditLog.log_event(
                    user_id=user.id,
                    event_type='backup_failed',
                    status='failure',
                    request_info=self._get_request_info()
                )
                return {'success': False, 'message': 'Invalid backup code'}
                
        except Exception as e:
            current_app.logger.error(f"Error verifying backup code: {str(e)}")
            return {'success': False, 'message': 'Verification failed'}
    
    def disable_2fa(self, user, password=None):
        """Disable 2FA for a user"""
        try:
            # Verify password if provided
            if password and not user.check_password(password):
                return {'success': False, 'message': 'Invalid password'}
            
            # Delete all 2FA methods
            TwoFactorMethod.query.filter_by(user_id=user.id).delete()
            
            # Delete backup codes
            TwoFactorBackupCode.query.filter_by(user_id=user.id).delete()
            
            # Revoke sessions
            TwoFactorSession.query.filter_by(user_id=user.id).update({
                'expires_at': datetime.utcnow()
            })
            
            # Update user
            user.two_factor_enabled = False
            user.two_factor_enabled_at = None
            
            db.session.commit()
            
            # Log event
            TwoFactorAuditLog.log_event(
                user_id=user.id,
                event_type='disabled',
                request_info=self._get_request_info()
            )
            
            return {'success': True, 'message': '2FA has been disabled'}
            
        except Exception as e:
            current_app.logger.error(f"Error disabling 2FA: {str(e)}")
            return {'success': False, 'message': 'Failed to disable 2FA'}
    
    def check_trusted_device(self, user, session_token=None):
        """Check if the current device is trusted"""
        try:
            if session_token:
                session = TwoFactorSession.query.filter_by(
                    user_id=user.id,
                    session_token=session_token
                ).first()
                
                if session and session.expires_at > datetime.utcnow():
                    session.last_activity = datetime.utcnow()
                    db.session.commit()
                    return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error checking trusted device: {str(e)}")
            return False
    
    # Helper methods
    def _format_phone_number(self, phone):
        """Format phone number for Zambia"""
        phone = ''.join(filter(str.isdigit, phone))
        if not phone.startswith('260'):
            if phone.startswith('0'):
                phone = '260' + phone[1:]
            else:
                phone = '260' + phone
        return '+' + phone
    
    def _send_sms_code(self, phone, code, user):
        """Send SMS verification code"""
        message = f"ONTECH ICT Management\nYour verification code is: {code}\nValid for 10 minutes.\nDial *388# for support."
        
        self.sms_service.send_sms(
            recipient=phone,
            message=message,
            sender_id='ONTECH'
        )
    
    def _send_email_code(self, email, code, user):
        """Send email verification code"""
        subject = "ONTECH - Your Verification Code"
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #000; color: white; padding: 20px; text-align: center;">
                <h2>ONTECH ICT Management System</h2>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Hello {user.full_name or user.username},</p>
                <p>Your verification code is:</p>
                <div style="background: white; border: 2px solid #000; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #000; font-size: 36px; letter-spacing: 5px; margin: 0;">{code}</h1>
                </div>
                <p>This code is valid for 10 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    ONTECH Solutions Limited<br>
                    Plot No. 25996, Kwacha Road, Olympia Park, Lusaka<br>
                    Tel: +260 211 488275 | *388# for Quick Access
                </p>
            </div>
        </div>
        """
        
        self.notification_service.send_notification(
            recipients=[email],
            subject=subject,
            message=body,
            notification_type='security',
            channels=['email']
        )
    
    def _generate_totp_qr(self, user, secret):
        """Generate TOTP QR code URL"""
        issuer = 'ONTECH ICT'
        label = f"{issuer}:{user.email}"
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=label,
            issuer_name=issuer
        )
        return uri
    
    def _mask_phone(self, phone):
        """Mask phone number for display"""
        if len(phone) > 6:
            return f"{phone[:4]}****{phone[-2:]}"
        return "****"
    
    def _mask_email(self, email):
        """Mask email for display"""
        parts = email.split('@')
        if len(parts) == 2:
            username = parts[0]
            if len(username) > 2:
                masked = username[0] + '*' * (len(username) - 2) + username[-1]
            else:
                masked = '*' * len(username)
            return f"{masked}@{parts[1]}"
        return "****"
    
    def _get_request_info(self):
        """Get request information"""
        if request:
            return {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        return {}
    
    def _get_device_info(self):
        """Get device information"""
        if request:
            return {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'name': self._parse_device_name(request.headers.get('User-Agent', '')),
                'fingerprint': None  # Can be implemented with JavaScript
            }
        return {}
    
    def _parse_device_name(self, user_agent):
        """Parse device name from user agent"""
        # Simple parsing - can be enhanced
        if 'Mobile' in user_agent:
            return 'Mobile Device'
        elif 'Tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'

# Create singleton instance
two_factor_service = TwoFactorService()