# services/sms_service.py - SMS Service Implementation
"""
SMS Service for Enterprise ICT Management System
Handles SMS notifications with multiple provider support (Twilio, Africa's Talking, etc.)
"""

from flask import current_app
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from threading import Thread
import logging
import os
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSService:
    """Centralized SMS service for the ICT Management System"""
    
    def __init__(self, app=None):
        self.app = app
        self.provider = None
        self.enabled = False
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize SMS service with Flask app"""
        self.app = app
        
        # Check if SMS is enabled
        self.enabled = app.config.get('ENABLE_SMS_ALERTS', False)
        
        if not self.enabled:
            logger.info("SMS service disabled in configuration")
            return
        
        # Get SMS configuration from environment variables
        sms_provider = app.config.get('SMS_PROVIDER') or os.getenv('SMS_PROVIDER', 'africas_talking')
        
        # Configure based on provider
        if sms_provider.lower() == 'twilio':
            self._init_twilio(app)
        elif sms_provider.lower() == 'africas_talking':
            self._init_africas_talking(app)
        elif sms_provider.lower() == 'nexmo':
            self._init_nexmo(app)
        elif sms_provider.lower() == 'cloudservicezm':
            self._init_cloudservicezm(app)
        else:
            logger.warning(f"Unknown SMS provider: {sms_provider}. SMS disabled.")
            self.enabled = False
            return
        
        self.provider = sms_provider.lower()
        logger.info(f"SMS service initialized with provider: {sms_provider}")
    
    def _init_twilio(self, app):
        """Initialize Twilio SMS provider"""
        try:
            import twilio
            from twilio.rest import Client
            
            account_sid = app.config.get('TWILIO_ACCOUNT_SID') or os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = app.config.get('TWILIO_AUTH_TOKEN') or os.getenv('TWILIO_AUTH_TOKEN')
            from_number = app.config.get('TWILIO_FROM_NUMBER') or os.getenv('TWILIO_FROM_NUMBER')
            
            if not all([account_sid, auth_token, from_number]):
                logger.error("Twilio credentials incomplete. SMS disabled.")
                self.enabled = False
                return
            
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
            logger.info(f"Twilio initialized - sending from: {from_number}")
            
        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {str(e)}")
            self.enabled = False
    
    def _init_africas_talking(self, app):
        """Initialize Africa's Talking SMS provider"""
        try:
            import africastalking
            
            username = app.config.get('AT_USERNAME') or os.getenv('AT_USERNAME', 'sandbox')
            api_key = app.config.get('AT_API_KEY') or os.getenv('AT_API_KEY')
            from_number = app.config.get('AT_FROM_NUMBER') or os.getenv('AT_FROM_NUMBER', 'ONTECH')
            
            if not api_key:
                logger.error("Africa's Talking API key missing. SMS disabled.")
                self.enabled = False
                return
            
            africastalking.initialize(username, api_key)
            self.client = africastalking.SMS
            self.from_number = from_number
            logger.info(f"Africa's Talking initialized - sending from: {from_number}")
            
        except ImportError:
            logger.error("Africa's Talking library not installed. Run: pip install africastalking")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking: {str(e)}")
            self.enabled = False
    
    def _init_nexmo(self, app):
        """Initialize Nexmo/Vonage SMS provider"""
        try:
            import nexmo
            
            api_key = app.config.get('NEXMO_API_KEY') or os.getenv('NEXMO_API_KEY')
            api_secret = app.config.get('NEXMO_API_SECRET') or os.getenv('NEXMO_API_SECRET')
            from_number = app.config.get('NEXMO_FROM_NUMBER') or os.getenv('NEXMO_FROM_NUMBER', 'ONTECH')
            
            if not all([api_key, api_secret]):
                logger.error("Nexmo credentials incomplete. SMS disabled.")
                self.enabled = False
                return
            
            self.client = nexmo.Client(key=api_key, secret=api_secret)
            self.from_number = from_number
            logger.info(f"Nexmo initialized - sending from: {from_number}")
            
        except ImportError:
            logger.error("Nexmo library not installed. Run: pip install nexmo")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Nexmo: {str(e)}")
            self.enabled = False
    
    def _init_cloudservicezm(self, app):
        """Initialize CloudServiceZM SMS provider"""
        try:
            api_url = app.config.get('CLOUDSERVICEZM_API_URL') or os.getenv('CLOUDSERVICEZM_API_URL')
            username = app.config.get('CLOUDSERVICEZM_USERNAME') or os.getenv('CLOUDSERVICEZM_USERNAME')
            password = app.config.get('CLOUDSERVICEZM_PASSWORD') or os.getenv('CLOUDSERVICEZM_PASSWORD')
            shortcode = app.config.get('CLOUDSERVICEZM_SHORTCODE') or os.getenv('CLOUDSERVICEZM_SHORTCODE')
            sender_id = app.config.get('CLOUDSERVICEZM_SENDER_ID') or os.getenv('CLOUDSERVICEZM_SENDER_ID', 'ONTECH')
            api_key = app.config.get('CLOUDSERVICEZM_API_KEY') or os.getenv('CLOUDSERVICEZM_API_KEY')
            
            if not all([api_url, username, password]):
                logger.error("CloudServiceZM credentials incomplete. SMS disabled.")
                self.enabled = False
                return
            
            self.api_url = api_url
            self.username = username
            self.password = password
            self.shortcode = shortcode
            self.sender_id = sender_id
            self.api_key = api_key
            self.from_number = sender_id
            
            logger.info(f"CloudServiceZM initialized - API: {api_url}")
            logger.info(f"CloudServiceZM - Sender ID: {sender_id}, Shortcode: {shortcode}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CloudServiceZM: {str(e)}")
            self.enabled = False
    
    def _send_async_sms(self, app, phone_numbers: List[str], message: str):
        """Send SMS asynchronously with proper app context"""
        with app.app_context():
            try:
                self._send_sms_sync(phone_numbers, message)
                logger.info(f"✅ SMS sent successfully to {phone_numbers}")
            except Exception as e:
                logger.error(f"❌ Failed to send async SMS to {phone_numbers}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def _send_sms_sync(self, phone_numbers: List[str], message: str):
        """Send SMS synchronously based on provider"""
        if not self.enabled:
            logger.warning("SMS service disabled - message not sent")
            return False
        
        success_count = 0
        
        for phone_number in phone_numbers:
            try:
                # Clean phone number
                clean_number = self._clean_phone_number(phone_number)
                if not clean_number:
                    logger.warning(f"Invalid phone number: {phone_number}")
                    continue
                
                # Send based on provider
                if self.provider == 'twilio':
                    result = self._send_twilio_sms(clean_number, message)
                elif self.provider == 'africas_talking':
                    result = self._send_africas_talking_sms(clean_number, message)
                elif self.provider == 'nexmo':
                    result = self._send_nexmo_sms(clean_number, message)
                elif self.provider == 'cloudservicezm':
                    result = self._send_cloudservicezm_sms(clean_number, message)
                else:
                    logger.error(f"Unknown provider: {self.provider}")
                    continue
                
                if result:
                    success_count += 1
                    logger.info(f"✅ SMS sent to {clean_number}")
                else:
                    logger.error(f"❌ Failed to send SMS to {clean_number}")
                    
            except Exception as e:
                logger.error(f"❌ Error sending SMS to {phone_number}: {str(e)}")
        
        return success_count > 0
    
    def _send_twilio_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via Twilio"""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            return message_obj.sid is not None
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False
    
    def _send_africas_talking_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via Africa's Talking"""
        try:
            response = self.client.send(message, [phone_number], self.from_number)
            return response['SMSMessageData']['Recipients'][0]['status'] == 'Success'
        except Exception as e:
            logger.error(f"Africa's Talking SMS error: {str(e)}")
            return False
    
    def _send_nexmo_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via Nexmo"""
        try:
            response = self.client.send_message({
                'from': self.from_number,
                'to': phone_number,
                'text': message
            })
            return response['messages'][0]['status'] == '0'
        except Exception as e:
            logger.error(f"Nexmo SMS error: {str(e)}")
            return False
    
    def _send_cloudservicezm_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via CloudServiceZM HTTP API"""
        try:
            # Prepare API parameters based on the provided URL structure
            params = {
                'username': self.username,
                'password': self.password,
                'msg': message,
                'shortcode': self.shortcode,
                'sender_id': self.sender_id,
                'phone': phone_number.replace('+', ''),  # Remove + from phone number
                'api_key': self.api_key
            }
            
            logger.info(f"Sending SMS via CloudServiceZM to {phone_number}")
            logger.debug(f"CloudServiceZM API params: {params}")
            
            # Make HTTP GET request (based on the URL structure you provided)
            response = requests.get(self.api_url, params=params, timeout=30)
            
            logger.info(f"CloudServiceZM API response: {response.status_code}")
            logger.debug(f"CloudServiceZM response text: {response.text}")
            
            # Check if request was successful
            if response.status_code == 200:
                # Parse response - CloudServiceZM might return specific success indicators
                response_text = response.text.lower()
                
                # Common success indicators in SMS APIs
                success_indicators = [
                    'success', 'sent', 'delivered', 'ok', 'accepted', 
                    'queued', 'processed', '1001', 'message sent'
                ]
                
                if any(indicator in response_text for indicator in success_indicators):
                    logger.info(f"✅ CloudServiceZM SMS sent successfully to {phone_number}")
                    return True
                else:
                    logger.warning(f"⚠️ CloudServiceZM SMS status unclear: {response.text}")
                    # Return True if status code is 200 even if response is unclear
                    return True
            else:
                logger.error(f"❌ CloudServiceZM API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("CloudServiceZM API timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("CloudServiceZM API connection error")
            return False
        except Exception as e:
            logger.error(f"CloudServiceZM SMS error: {str(e)}")
            return False
    
    def _clean_phone_number(self, phone_number: str) -> Optional[str]:
        """Clean and validate phone number"""
        if not phone_number:
            return None
        
        # Remove all non-numeric characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Ensure it starts with + for international format
        if not cleaned.startswith('+'):
            # Add Zambia country code if no country code present
            if len(cleaned) == 9 and cleaned.startswith('9'):  # Zambian mobile format
                cleaned = '+260' + cleaned
            elif len(cleaned) == 10 and cleaned.startswith('09'):  # Alternative format
                cleaned = '+260' + cleaned[1:]
            else:
                cleaned = '+260' + cleaned  # Default to Zambia
        
        # Validate length (should be reasonable for international numbers)
        if len(cleaned) < 10 or len(cleaned) > 15:
            return None
        
        return cleaned
    
    def send_sms(self, phone_numbers: Union[str, List[str]], message: str, 
                 async_send: bool = True) -> bool:
        """
        Send SMS with comprehensive options
        
        Args:
            phone_numbers: Single phone number or list of phone numbers
            message: SMS message content (max 160 chars recommended)
            async_send: Whether to send asynchronously
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("SMS service disabled - message not sent")
            return False
        
        # CRITICAL FIX: Ensure we're in app context
        if not self.app:
            logger.error("No Flask app instance available")
            return False
        
        # Convert single number to list
        if isinstance(phone_numbers, str):
            phone_numbers = [phone_numbers]
        
        # Filter valid numbers
        valid_numbers = []
        for number in phone_numbers:
            clean_number = self._clean_phone_number(number)
            if clean_number:
                valid_numbers.append(clean_number)
        
        if not valid_numbers:
            logger.warning("No valid phone numbers provided")
            return False
        
        # Truncate message if too long
        if len(message) > 160:
            message = message[:157] + "..."
            logger.warning("SMS message truncated to 160 characters")
        
        logger.info(f"📱 Sending SMS to {len(valid_numbers)} recipients")
        logger.info(f"📱 Message: {message[:50]}...")
        
        try:
            if async_send and self.app:
                # Send asynchronously
                logger.info("📱 Sending SMS asynchronously...")
                thread = Thread(target=self._send_async_sms, args=(self.app, valid_numbers, message))
                thread.start()
                return True
            else:
                # Send synchronously
                logger.info("📱 Sending SMS synchronously...")
                return self._send_sms_sync(valid_numbers, message)
        
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==========================================================================
    # HELPER METHODS FOR GETTING PHONE NUMBERS
    # ==========================================================================
    
    def _get_it_admin_phones(self) -> List[str]:
        """Get IT administrator phone numbers"""
        try:
            with self.app.app_context():
                from models import db, User
                
                phones = []
                try:
                    admins = User.query.filter_by(is_admin=True, is_active=True).all()
                    phones = [admin.phone for admin in admins if admin.phone]
                    logger.info(f"Found {len(phones)} admin phone numbers: {phones}")
                except Exception as db_error:
                    logger.warning(f"Could not query User model: {db_error}")
                
                # Fallback to configured admin phones
                if not phones:
                    phones = ['+260977123456', '+260966789012']  # Example Zambian numbers
                    logger.info(f"Using fallback admin phones: {phones}")
                
                return phones
        except Exception as e:
            logger.error(f"Error getting IT admin phones: {str(e)}")
            return ['+260977123456']  # Emergency fallback
    
    def _get_management_phones(self) -> List[str]:
        """Get management phone numbers"""
        try:
            with self.app.app_context():
                from models import db, User
                
                phones = []
                try:
                    managers = User.query.filter(
                        db.or_(
                            User.department.ilike('%management%'),
                            User.department.ilike('%director%'),
                            User.department.ilike('%executive%'),
                            User.is_admin == True
                        )
                    ).filter_by(is_active=True).all()
                    
                    phones = [manager.phone for manager in managers if manager.phone]
                    logger.info(f"Found {len(phones)} management phone numbers")
                except Exception as db_error:
                    logger.warning(f"Could not query for management users: {db_error}")
                
                # Fallback
                if not phones:
                    phones = ['+260977555666', '+260966444333']
                    logger.info(f"Using fallback management phones: {phones}")
                
                return phones
        except Exception as e:
            logger.error(f"Error getting management phones: {str(e)}")
            return ['+260977555666']
    
    def _get_security_phones(self) -> List[str]:
        """Get security team phone numbers"""
        try:
            with self.app.app_context():
                from models import db, User
                
                phones = []
                try:
                    security_users = User.query.filter(
                        User.department.ilike('%security%')
                    ).filter_by(is_active=True).all()
                    
                    phones = [user.phone for user in security_users if user.phone]
                    logger.info(f"Found {len(phones)} security phone numbers")
                except Exception as db_error:
                    logger.warning(f"Could not query for security users: {db_error}")
                
                # Fallback
                if not phones:
                    phones = ['+260977777888']
                    logger.info(f"Using fallback security phones: {phones}")
                
                return phones
        except Exception as e:
            logger.error(f"Error getting security phones: {str(e)}")
            return ['+260977777888']
    
    # ==========================================================================
    # SMS NOTIFICATION METHODS
    # ==========================================================================
    
    def send_critical_system_alert(self, alert_type: str, message: str):
        """Send critical system alert via SMS"""
        try:
            logger.info(f"📱 Sending critical SMS alert: {alert_type}")
            
            recipients = self._get_it_admin_phones()
            recipients.extend(self._get_management_phones())
            recipients = list(set(recipients))  # Remove duplicates
            
            sms_message = f"🚨 CRITICAL ALERT: {alert_type}\n{message}\n- Ontech ICT System"
            
            result = self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
            logger.info(f"📱 Critical alert SMS result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send critical SMS alert: {str(e)}")
            return False
    
    def send_security_incident_alert(self, incident_type: str, details: str):
        """Send security incident alert via SMS"""
        try:
            logger.info(f"📱 Sending security incident SMS: {incident_type}")
            
            recipients = self._get_security_phones()
            recipients.extend(self._get_it_admin_phones())
            recipients = list(set(recipients))
            
            sms_message = f"🔒 SECURITY ALERT: {incident_type}\n{details}\nImmediate action required.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send security incident SMS: {str(e)}")
            return False
    
    def send_network_outage_alert(self, affected_systems: List[str], estimated_downtime: str = "Unknown"):
        """Send network outage alert via SMS"""
        try:
            logger.info(f"📱 Sending network outage SMS for {len(affected_systems)} systems")
            
            recipients = self._get_it_admin_phones()
            
            systems_text = ", ".join(affected_systems[:3])  # Limit for SMS length
            if len(affected_systems) > 3:
                systems_text += f" and {len(affected_systems) - 3} more"
            
            sms_message = f"🌐 NETWORK OUTAGE: {systems_text}\nETA: {estimated_downtime}\nCheck email for details.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send network outage SMS: {str(e)}")
            return False
    
    def send_maintenance_reminder(self, maintenance_type: str, scheduled_time: str, contact_phone: str = None):
        """Send maintenance reminder via SMS"""
        try:
            logger.info(f"📱 Sending maintenance reminder SMS")
            
            recipients = []
            if contact_phone:
                recipients.append(contact_phone)
            else:
                recipients = self._get_it_admin_phones()
            
            sms_message = f"🔧 MAINTENANCE REMINDER: {maintenance_type}\nScheduled: {scheduled_time}\nPrepare systems accordingly.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send maintenance reminder SMS: {str(e)}")
            return False
    
    def send_backup_failure_alert(self, backup_type: str, failure_reason: str):
        """Send backup failure alert via SMS"""
        try:
            logger.info(f"📱 Sending backup failure SMS: {backup_type}")
            
            recipients = self._get_it_admin_phones()
            
            sms_message = f"💾 BACKUP FAILED: {backup_type}\nReason: {failure_reason}\nImmediate attention required.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send backup failure SMS: {str(e)}")
            return False
    
    def send_license_expiry_urgent(self, software_name: str, days_remaining: int):
        """Send urgent license expiry alert via SMS"""
        try:
            logger.info(f"📱 Sending urgent license expiry SMS: {software_name}")
            
            recipients = self._get_it_admin_phones()
            recipients.extend(self._get_management_phones())
            recipients = list(set(recipients))
            
            sms_message = f"📄 LICENSE URGENT: {software_name} expires in {days_remaining} day(s)!\nRenew immediately to avoid disruption.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=recipients,
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send license expiry SMS: {str(e)}")
            return False
    
    def send_two_factor_auth_code(self, phone_number: str, code: str):
        """Send 2FA verification code via SMS"""
        try:
            logger.info(f"📱 Sending 2FA code SMS to {phone_number[-4:]}")  # Log last 4 digits only
            
            sms_message = f"Your Ontech ICT verification code is: {code}\nThis code expires in 5 minutes.\nDo not share this code with anyone."
            
            return self.send_sms(
                phone_numbers=[phone_number],
                message=sms_message,
                async_send=False  # 2FA codes should be sent immediately
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send 2FA code SMS: {str(e)}")
            return False
    
    def send_password_reset_notification(self, phone_number: str, username: str):
        """Send password reset notification via SMS"""
        try:
            logger.info(f"📱 Sending password reset SMS to {phone_number[-4:]}")
            
            sms_message = f"Password reset requested for {username} on Ontech ICT system.\nIf this wasn't you, contact IT immediately.\n- Ontech ICT"
            
            return self.send_sms(
                phone_numbers=[phone_number],
                message=sms_message,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send password reset SMS: {str(e)}")
            return False
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def get_sms_stats(self) -> Dict:
        """Get SMS service statistics"""
        return {
            'enabled': self.enabled,
            'provider': self.provider if self.enabled else None,
            'from_number': getattr(self, 'from_number', None) if self.enabled else None,
            'service_status': 'Active' if self.enabled else 'Disabled'
        }
    
    def test_sms_service(self, phone_number: str) -> bool:
        """Test SMS service with a simple message"""
        try:
            test_message = f"SMS service test from Ontech ICT Management System. Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = self.send_sms(
                phone_numbers=[phone_number],
                message=test_message,
                async_send=False
            )
            
            logger.info(f"SMS test result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"SMS test failed: {str(e)}")
            return False


# Create global SMS service instance
sms_service = SMSService()


# ==========================================================================
# INTEGRATION FUNCTION FOR FLASK APP
# ==========================================================================

def init_sms_service(app):
    """Initialize SMS service with Flask app"""
    sms_service.init_app(app)
    return sms_service