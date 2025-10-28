# services/email_service.py - COMPLETE FINAL VERSION
"""
Email Service for Enterprise ICT Management System
Handles all email notifications with proper Flask app context
ALL EMAILS SENT FROM: no_reply@ontech.co.zm (configured in .env)
"""

from flask import current_app, render_template_string
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from jinja2 import Template
import logging
import os
from typing import List, Dict, Optional, Union
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Centralized email service for the ICT Management System"""
    
    def __init__(self, app=None):
        self.mail = None
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.app = app
        
        # Get email configuration from environment variables or use defaults
        mail_server = app.config.get('MAIL_SERVER') or os.getenv('MAIL_SERVER', 'smtp.titan.email')
        mail_port = app.config.get('MAIL_PORT') or int(os.getenv('MAIL_PORT', '587'))
        mail_username = app.config.get('MAIL_USERNAME') or os.getenv('MAIL_USERNAME', 'no_reply@ontech.co.zm')
        mail_password = app.config.get('MAIL_PASSWORD') or os.getenv('MAIL_PASSWORD', 'TestPass123!')
        mail_use_tls = app.config.get('MAIL_USE_TLS', True)
        mail_use_ssl = app.config.get('MAIL_USE_SSL', False)
        
        # Configure Flask-Mail - ALL EMAILS FROM SINGLE ADDRESS
        app.config.update({
            'MAIL_SERVER': mail_server,
            'MAIL_PORT': mail_port,
            'MAIL_USE_TLS': mail_use_tls,
            'MAIL_USE_SSL': mail_use_ssl,
            'MAIL_USERNAME': mail_username,
            'MAIL_PASSWORD': mail_password,
            'MAIL_DEFAULT_SENDER': ('Ontech ICT Management System', mail_username),
            'MAIL_SUPPRESS_SEND': app.config.get('TESTING', False),
            'MAIL_DEBUG': app.config.get('DEBUG', False)
        })
        
        self.mail = Mail(app)
        logger.info(f"Email service initialized - ALL emails will be sent from: {mail_username}")
        logger.info(f"Email server: {mail_server}:{mail_port}")
    
    def _send_async_email(self, app, msg):
        """Send email asynchronously with proper app context"""
        with app.app_context():
            try:
                self.mail.send(msg)
                logger.info(f"✅ Email sent successfully to {msg.recipients}")
            except Exception as e:
                logger.error(f"❌ Failed to send email to {msg.recipients}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def send_email(self, subject: str, recipients: List[str], 
                   html_body: str = None, text_body: str = None,
                   sender: str = None, cc: List[str] = None, bcc: List[str] = None,
                   attachments: List[Dict] = None, async_send: bool = True):
        """
        Send email with comprehensive options
        ALL EMAILS SENT FROM: no_reply@ontech.co.zm (ignores sender parameter)
        """
        # CRITICAL FIX: Ensure we're in app context
        if not self.app:
            logger.error("No Flask app instance available")
            return False
        
        # Use app context for all operations
        with self.app.app_context():
            try:
                if not recipients:
                    logger.warning("No recipients provided for email")
                    return False
                
                # Filter out invalid email addresses
                valid_recipients = [email for email in recipients if email and '@' in email and '.' in email]
                if not valid_recipients:
                    logger.warning("No valid email addresses found")
                    return False
                
                # ALWAYS use the configured email address from .env - IGNORE sender parameter
                mail_username = self.app.config.get('MAIL_USERNAME', 'no_reply@ontech.co.zm')
                consistent_sender = ('Ontech ICT Management System', mail_username)
                
                logger.info(f"📧 Sending email from {mail_username} to {valid_recipients}")
                logger.info(f"📧 Subject: {subject}")
                
                msg = Message(
                    subject=subject,
                    sender=consistent_sender,
                    recipients=valid_recipients,
                    cc=cc or [],
                    bcc=bcc or []
                )
                
                if html_body:
                    msg.html = html_body
                if text_body:
                    msg.body = text_body
                
                # Add attachments if provided
                if attachments:
                    for attachment in attachments:
                        msg.attach(
                            attachment.get('filename', 'attachment'),
                            attachment.get('content_type', 'application/octet-stream'),
                            attachment.get('data', b'')
                        )
                
                if async_send and self.app:
                    # Send asynchronously
                    logger.info("📧 Sending email asynchronously...")
                    thread = Thread(target=self._send_async_email, args=(self.app, msg))
                    thread.start()
                else:
                    # Send synchronously
                    logger.info("📧 Sending email synchronously...")
                    self.mail.send(msg)
                    logger.info(f"✅ Email sent successfully from {mail_username} to {valid_recipients}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to send email from {mail_username}: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    
    # ==========================================================================
    # HELPER METHODS - FIXED WITH APP CONTEXT AND USER MODEL COMPATIBILITY
    # ==========================================================================
    
    def _get_it_admin_emails(self) -> List[str]:
        """Get IT administrator email addresses - FIXED"""
        try:
            with self.app.app_context():
                from models import db, User
                
                # Try to get from User model - check if it has required fields
                try:
                    admins = User.query.filter_by(is_admin=True, is_active=True).all()
                    emails = [admin.email for admin in admins if admin.email and '@' in admin.email]
                    logger.info(f"Found {len(emails)} admin emails from database: {emails}")
                except Exception as db_error:
                    logger.warning(f"Could not query User model: {db_error}")
                    emails = []
                
                # Try UserAccount model if User model failed
                if not emails:
                    try:
                        from models import UserAccount
                        user_admins = UserAccount.query.filter_by(is_admin=True, is_active=True).all()
                        emails = [admin.email for admin in user_admins if admin.email and '@' in admin.email]
                        logger.info(f"Found {len(emails)} admin emails from UserAccount: {emails}")
                    except Exception:
                        pass
                
                # Fallback to configured admin emails
                if not emails:
                    emails = ['admin@ontech.co.zm', 'it-support@ontech.co.zm']
                    logger.info(f"Using fallback admin emails: {emails}")
                
                return emails
        except Exception as e:
            logger.error(f"Error getting IT admin emails: {str(e)}")
            return ['admin@ontech.co.zm']
    
    def _get_management_emails(self) -> List[str]:
        """Get management email addresses - FIXED"""
        try:
            with self.app.app_context():
                from models import db, User
                
                emails = []
                try:
                    # Try to get managers from database using department (not role)
                    managers = User.query.filter(
                        db.or_(
                            User.department.ilike('%management%'),
                            User.department.ilike('%director%'),
                            User.department.ilike('%executive%'),
                            User.department.ilike('%manager%'),
                            User.is_admin == True  # Include admins as management
                        )
                    ).filter_by(is_active=True).all()
                    
                    emails = [manager.email for manager in managers if manager.email and '@' in manager.email]
                    logger.info(f"Found {len(emails)} management emails: {emails}")
                except Exception as db_error:
                    logger.warning(f"Could not query for management users: {db_error}")
                
                # Fallback to configured management emails
                if not emails:
                    emails = ['management@ontech.co.zm', 'director@ontech.co.zm']
                    logger.info(f"Using fallback management emails: {emails}")
                
                return emails
        except Exception as e:
            logger.error(f"Error getting management emails: {str(e)}")
            return ['management@ontech.co.zm']
    
    def _get_helpdesk_emails(self) -> List[str]:
        """Get help desk team email addresses - FIXED"""
        try:
            with self.app.app_context():
                from models import db, User
                
                emails = []
                try:
                    # Try to get helpdesk users from database using department only
                    helpdesk_users = User.query.filter(
                        db.or_(
                            User.department.ilike('%helpdesk%'),
                            User.department.ilike('%support%'),
                            User.department.ilike('%help desk%'),
                            User.department.ilike('%service desk%')
                        )
                    ).filter_by(is_active=True).all()
                    
                    emails = [user.email for user in helpdesk_users if user.email and '@' in user.email]
                    logger.info(f"Found {len(emails)} helpdesk emails: {emails}")
                except Exception as db_error:
                    logger.warning(f"Could not query for helpdesk users: {db_error}")
                
                # Fallback to configured helpdesk emails
                if not emails:
                    emails = ['helpdesk@ontech.co.zm', 'support@ontech.co.zm']
                    logger.info(f"Using fallback helpdesk emails: {emails}")
                
                return emails
        except Exception as e:
            logger.error(f"Error getting helpdesk emails: {str(e)}")
            return ['helpdesk@ontech.co.zm']
    
    def _get_security_emails(self) -> List[str]:
        """Get security team email addresses - FIXED"""
        try:
            with self.app.app_context():
                from models import db, User
                
                emails = []
                try:
                    # Try to get security users from database using department only
                    security_users = User.query.filter(
                        User.department.ilike('%security%')
                    ).filter_by(is_active=True).all()
                    
                    emails = [user.email for user in security_users if user.email and '@' in user.email]
                    logger.info(f"Found {len(emails)} security emails: {emails}")
                except Exception as db_error:
                    logger.warning(f"Could not query for security users: {db_error}")
                
                # Fallback to configured security emails
                if not emails:
                    emails = ['security@ontech.co.zm', 'infosec@ontech.co.zm']
                    logger.info(f"Using fallback security emails: {emails}")
                
                return emails
        except Exception as e:
            logger.error(f"Error getting security emails: {str(e)}")
            return ['security@ontech.co.zm']
    
    # ==========================================================================
    # EMAIL TRIGGERS - ALL UPDATED WITH PROPER CONTEXT AND LOGGING
    # ==========================================================================
    
    def send_ticket_created_notification(self, ticket):
        """Send notification when new ticket is created"""
        try:
            logger.info(f"📧 Preparing ticket creation email for: {ticket.ticket_number}")
            
            subject = f"New Help Desk Ticket: {ticket.ticket_number} - {ticket.title}"
            recipients = self._get_helpdesk_emails()
            
            logger.info(f"📧 Ticket notification recipients: {recipients}")
            
            # Send confirmation to requester first
            if ticket.requester and '@' in ticket.requester:
                logger.info(f"📧 Sending confirmation to requester: {ticket.requester}")
                self.send_ticket_confirmation_to_requester(ticket)
            
            # Prepare template context
            template_context = {
                'ticket': ticket,
                'created_date': ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            html_body = self._render_template('ticket_created', template_context)
            
            result = self.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                async_send=True
            )
            
            logger.info(f"📧 Ticket creation email result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send ticket creation notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_ticket_confirmation_to_requester(self, ticket):
        """Send confirmation email to ticket requester"""
        try:
            if not ticket.requester or '@' not in ticket.requester:
                logger.warning("No valid requester email for ticket confirmation")
                return False
            
            subject = f"Ticket Confirmation: {ticket.ticket_number} - {ticket.title}"
            
            template_context = {
                'ticket': ticket,
                'created_date': ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            html_body = self._render_template('ticket_confirmation', template_context)
            
            result = self.send_email(
                subject=subject,
                recipients=[ticket.requester],
                html_body=html_body,
                async_send=True
            )
            
            logger.info(f"📧 Ticket confirmation email to requester result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send ticket confirmation: {str(e)}")
            return False
    
    def send_user_account_notification(self, user_data: Dict, action: str):
        """Send user account related notifications"""
        try:
            logger.info(f"📧 Preparing user account email for: {user_data.get('username')} - {action}")
            
            action_messages = {
                'created': 'New User Account Created',
                'activated': 'User Account Activated',
                'deactivated': 'User Account Deactivated',
                'password_reset': 'Password Reset Request',
                'login': 'User Login Notification'
            }
            
            subject = f"{action_messages.get(action, 'User Account Update')}: {user_data.get('username', 'Unknown')}"
            
            recipients = []
            
            # Add user's email if available
            if user_data.get('email') and '@' in user_data.get('email', ''):
                recipients.append(user_data['email'])
            
            # Add IT admin emails for certain actions
            if action in ['created', 'activated', 'deactivated']:
                admin_emails = self._get_it_admin_emails()
                recipients.extend(admin_emails)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            logger.info(f"📧 User account notification recipients: {recipients}")
            
            template_context = {
                'user_data': user_data,
                'action': action,
                'action_message': action_messages.get(action, 'User Account Update'),
                'action_time': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            html_body = self._render_template('user_account', template_context)
            
            result = self.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                async_send=True
            )
            
            logger.info(f"📧 User account notification result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send user account notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_asset_assignment_notification(self, asset, assigned_user: str, 
                                         assigned_by: str, assignment_type: str = "Assignment"):
        """Send notification when asset is assigned to user"""
        try:
            logger.info(f"📧 Preparing asset assignment email for: {getattr(asset, 'asset_tag', 'Unknown')}")
            
            subject = f"Asset Assignment: {getattr(asset, 'name', 'Unknown Asset')} ({getattr(asset, 'asset_tag', 'N/A')})"
            
            recipients = []
            
            # Add asset end-user email if available
            if hasattr(asset, 'end_user_email') and asset.end_user_email and '@' in asset.end_user_email:
                recipients.append(asset.end_user_email)
            
            # Add asset manager email if available
            if hasattr(asset, 'end_user_manager_email') and asset.end_user_manager_email and '@' in asset.end_user_manager_email:
                recipients.append(asset.end_user_manager_email)
            
            # Get IT admin emails
            admin_emails = self._get_it_admin_emails()
            
            logger.info(f"📧 Asset assignment recipients: {recipients}")
            logger.info(f"📧 Asset assignment CC (admins): {admin_emails}")
            
            template_context = {
                'asset': asset,
                'assigned_user': assigned_user,
                'assigned_by': assigned_by,
                'assignment_type': assignment_type,
                'assignment_date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            html_body = self._render_template('asset_assignment', template_context)
            
            result = self.send_email(
                subject=subject,
                recipients=recipients if recipients else admin_emails,  # Use admins if no direct recipients
                html_body=html_body,
                cc=admin_emails if recipients else None,
                async_send=True
            )
            
            logger.info(f"📧 Asset assignment notification result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send asset assignment notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_maintenance_completion_report(self, schedule, work_performed: str, issues_found: str = None):
        """Send maintenance completion notification"""
        try:
            logger.info(f"📧 Preparing maintenance completion email")
            
            asset_name = "Unknown Asset"
            if hasattr(schedule, 'asset') and schedule.asset:
                asset_name = getattr(schedule.asset, 'name', 'Unknown Asset')
            
            subject = f"Maintenance Completed: {asset_name}"
            recipients = self._get_it_admin_emails()
            
            # Add asset end-user if applicable
            if hasattr(schedule, 'asset') and schedule.asset and hasattr(schedule.asset, 'end_user_email') and schedule.asset.end_user_email:
                if '@' in schedule.asset.end_user_email:
                    recipients.append(schedule.asset.end_user_email)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            logger.info(f"📧 Maintenance completion recipients: {recipients}")
            
            template_context = {
                'schedule': schedule,
                'work_performed': work_performed,
                'issues_found': issues_found,
                'completion_date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            html_body = self._render_template('maintenance_completion', template_context)
            
            result = self.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                async_send=True
            )
            
            logger.info(f"📧 Maintenance completion notification result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send maintenance completion report: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==========================================================================
    # ADDITIONAL EMAIL TRIGGERS
    # ==========================================================================
    
    def send_license_expiry_alert(self, licenses: List, days_until_expiry: int):
        """Send license expiry alert"""
        try:
            if not licenses:
                return False
            
            logger.info(f"📧 Sending license expiry alert for {len(licenses)} licenses")
            
            subject = f"License Expiry Alert - {len(licenses)} License(s) Expiring in {days_until_expiry} Days"
            recipients = self._get_it_admin_emails()
            recipients.extend(self._get_management_emails())
            recipients = list(set(recipients))  # Remove duplicates
            
            template_context = {
                'licenses': licenses,
                'days_until_expiry': days_until_expiry,
                'total_licenses': len(licenses)
            }
            
            html_body = self._render_template('license_expiry', template_context)
            
            return self.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send license expiry alert: {str(e)}")
            return False
    
    def send_system_alert(self, alert_type: str, message: str, severity: str = "Medium"):
        """Send general system alert"""
        try:
            logger.info(f"📧 Sending system alert: {alert_type}")
            
            subject = f"System Alert ({severity}): {alert_type}"
            
            # Determine recipients based on severity
            if severity.lower() in ['critical', 'high']:
                recipients = self._get_it_admin_emails()
                recipients.extend(self._get_management_emails())
            else:
                recipients = self._get_it_admin_emails()
            
            recipients = list(set(recipients))  # Remove duplicates
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                        <h1>System Alert - {severity}</h1>
                    </div>
                    <div style="padding: 20px;">
                        <h2>{alert_type}</h2>
                        <p>{message}</p>
                        <p><strong>Severity:</strong> {severity}</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self.send_email(
                subject=subject,
                recipients=recipients,
                html_body=html_body,
                async_send=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send system alert: {str(e)}")
            return False
    
    # ==========================================================================
    # TEMPLATE RENDERING - ENHANCED WITH BETTER ERROR HANDLING
    # ==========================================================================
    
    def _render_template(self, template_name: str, context: Dict) -> str:
        """Render email template with context data"""
        try:
            logger.info(f"📧 Rendering template: {template_name}")
            
            templates = {
                'asset_assignment': self._get_asset_assignment_template(),
                'ticket_created': self._get_ticket_created_template(),
                'ticket_confirmation': self._get_ticket_confirmation_template(),
                'maintenance_completion': self._get_maintenance_completion_template(),
                'user_account': self._get_user_account_template(),
                'license_expiry': self._get_license_expiry_template()
            }
            
            template_html = templates.get(template_name, self._get_default_template())
            
            if not template_html:
                logger.warning(f"Template {template_name} not found, using default")
                template_html = self._get_default_template()
            
            template = Template(template_html)
            rendered = template.render(**context)
            
            logger.info(f"📧 Template {template_name} rendered successfully ({len(rendered)} chars)")
            return rendered
            
        except Exception as e:
            logger.error(f"❌ Error rendering template {template_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return a simple fallback template
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                        <h1>Ontech ICT Management</h1>
                        <p>System Notification</p>
                    </div>
                    <div style="padding: 20px;">
                        <h2>Notification</h2>
                        <p>A system notification was generated but the template could not be rendered.</p>
                        <p><strong>Template:</strong> {template_name}</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px;">
                        <p>This is an automated message from Ontech ICT Management System</p>
                    </div>
                </div>
            </body>
            </html>
            """
    
    # ==========================================================================
    # EMAIL TEMPLATES - ENHANCED AND STANDARDIZED
    # ==========================================================================
    
    def _get_ticket_created_template(self) -> str:
        """Enhanced ticket creation template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Help Desk Ticket</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <!-- Header -->
                <div style="background-color: #17a2b8; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: bold;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">New Help Desk Ticket</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 30px 20px;">
                    <h2 style="color: #17a2b8; margin-top: 0; font-size: 24px;">New Help Desk Ticket Created</h2>
                    <p style="font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
                        A new support ticket has been submitted and requires attention from the help desk team.
                    </p>
                    
                    <!-- Ticket Details Box -->
                    <div style="background-color: #e7f3ff; border-left: 5px solid #17a2b8; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #0c5460; font-size: 18px;">Ticket Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; width: 140px;">Ticket Number:</td>
                                <td style="padding: 8px 0;">{{ ticket.ticket_number }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Title:</td>
                                <td style="padding: 8px 0;">{{ ticket.title }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Category:</td>
                                <td style="padding: 8px 0;">{{ ticket.category }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Priority:</td>
                                <td style="padding: 8px 0;">
                                    <span style="background-color: {% if ticket.priority == 'Critical' %}#dc3545{% elif ticket.priority == 'High' %}#fd7e14{% elif ticket.priority == 'Medium' %}#ffc107{% else %}#28a745{% endif %}; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">
                                        {{ ticket.priority }}
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Requester:</td>
                                <td style="padding: 8px 0;">{{ ticket.requester }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Created Date:</td>
                                <td style="padding: 8px 0;">{{ created_date }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Description Box -->
                    <div style="background-color: white; padding: 20px; margin: 25px 0; border-radius: 5px; border: 1px solid #dee2e6;">
                        <h4 style="margin-top: 0; color: #17a2b8; font-size: 16px;">Description</h4>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 3px; font-family: monospace; font-size: 14px; line-height: 1.4;">
                            {{ ticket.description }}
                        </div>
                    </div>
                    
                    <!-- Action Required -->
                    <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin: 25px 0; border-radius: 5px;">
                        <h4 style="margin-top: 0; color: #856404; font-size: 16px;">📋 Action Required</h4>
                        <p style="margin-bottom: 0; color: #856404;">
                            Please review this ticket and assign it to the appropriate team member for resolution.
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">
                        This is an automated message from Ontech ICT Management System
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">
                        Please do not reply to this email - no_reply@ontech.co.zm
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_ticket_confirmation_template(self) -> str:
        """Enhanced ticket confirmation template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ticket Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #28a745; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Ticket Confirmation</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #28a745; margin-top: 0;">✅ Your Ticket Has Been Created</h2>
                    <p style="font-size: 16px; line-height: 1.5;">
                        Thank you for contacting our support team. Your ticket has been successfully created and our team will review it shortly.
                    </p>
                    
                    <div style="background-color: #d4edda; border-left: 5px solid #28a745; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #155724;">Your Ticket Reference</h3>
                        <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">{{ ticket.ticket_number }}</p>
                        <p style="margin-bottom: 0;"><strong>Title:</strong> {{ ticket.title }}</p>
                        <p style="margin: 5px 0 0 0;"><strong>Created:</strong> {{ created_date }}</p>
                    </div>
                    
                    <h3 style="color: #17a2b8;">What happens next?</h3>
                    <ul style="line-height: 1.6;">
                        <li>Our support team will review your ticket</li>
                        <li>You will receive updates via email as we work on your request</li>
                        <li>Please keep your ticket number for reference</li>
                    </ul>
                    
                    <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                        If you need to provide additional information, please reply to this email with your ticket number.
                    </p>
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">Ontech ICT Management System</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_user_account_template(self) -> str:
        """Enhanced user account notification template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>User Account Notification</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #6f42c1; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">User Account Notification</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #6f42c1; margin-top: 0;">👤 {{ action_message }}</h2>
                    
                    <div style="background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #495057;">Account Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; width: 120px;">Username:</td>
                                <td style="padding: 8px 0;">{{ user_data.username }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Full Name:</td>
                                <td style="padding: 8px 0;">{{ user_data.full_name or 'Not specified' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                                <td style="padding: 8px 0;">{{ user_data.email }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Department:</td>
                                <td style="padding: 8px 0;">{{ user_data.department or 'Not specified' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Action Time:</td>
                                <td style="padding: 8px 0;">{{ action_time }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    {% if action == 'created' %}
                    <div style="background-color: #d1ecf1; border-left: 5px solid #17a2b8; padding: 15px; margin: 25px 0; border-radius: 5px;">
                        <h4 style="margin-top: 0; color: #0c5460;">📝 Next Steps</h4>
                        <p style="margin-bottom: 0;">The new user account is now active and ready for use. The user should receive their login credentials separately.</p>
                    </div>
                    {% endif %}
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">Ontech ICT Management System</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_asset_assignment_template(self) -> str:
        """Enhanced asset assignment template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Asset Assignment</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #fd7e14; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Asset Assignment Notification</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #fd7e14; margin-top: 0;">📦 Asset {{ assignment_type }}</h2>
                    <p style="font-size: 16px; line-height: 1.5;">
                        Dear {{ assigned_user }},<br>
                        An asset has been {{ assignment_type.lower() }}ed to you. Please review the details below:
                    </p>
                    
                    <div style="background-color: #fff3cd; border-left: 5px solid #fd7e14; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #856404;">Asset Information</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; width: 140px;">Asset Tag:</td>
                                <td style="padding: 8px 0; font-family: monospace; background-color: #f8f9fa; padding: 4px 8px; border-radius: 3px;">{{ asset.asset_tag or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Asset Name:</td>
                                <td style="padding: 8px 0;">{{ asset.name or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Category:</td>
                                <td style="padding: 8px 0;">{{ asset.category or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Brand/Model:</td>
                                <td style="padding: 8px 0;">{{ asset.brand or 'N/A' }} {{ asset.model or '' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Serial Number:</td>
                                <td style="padding: 8px 0; font-family: monospace;">{{ asset.serial_number or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Location:</td>
                                <td style="padding: 8px 0;">{{ asset.location or 'N/A' }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #f8f9fa; border-left: 5px solid #6c757d; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #495057;">Assignment Details</h3>
                        <p style="margin: 5px 0;"><strong>Assigned By:</strong> {{ assigned_by }}</p>
                        <p style="margin: 5px 0;"><strong>Assignment Date:</strong> {{ assignment_date }}</p>
                        <p style="margin: 5px 0;"><strong>Assignment Type:</strong> {{ assignment_type }}</p>
                    </div>
                    
                    <div style="background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; margin: 25px 0; border-radius: 5px;">
                        <h4 style="margin-top: 0; color: #155724;">📋 Your Responsibilities</h4>
                        <ul style="margin-bottom: 0; color: #155724;">
                            <li>Ensure proper care and security of the assigned asset</li>
                            <li>Report any damage or issues immediately</li>
                            <li>Return the asset when no longer needed</li>
                            <li>Contact IT support for any technical assistance</li>
                        </ul>
                    </div>
                    
                    <p style="font-size: 14px; color: #6c757d;">
                        If you have any questions about this assignment or the asset, please contact the IT support team.
                    </p>
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">Ontech ICT Management System</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_maintenance_completion_template(self) -> str:
        """Enhanced maintenance completion template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Maintenance Completed</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #28a745; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Maintenance Completed</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #28a745; margin-top: 0;">✅ Maintenance Work Completed</h2>
                    
                    <div style="background-color: #d4edda; border-left: 5px solid #28a745; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #155724;">Work Summary</h3>
                        <p style="margin: 5px 0;"><strong>Completion Date:</strong> {{ completion_date }}</p>
                        <p style="margin: 5px 0;"><strong>Work Performed:</strong></p>
                        <div style="background-color: white; padding: 15px; border-radius: 3px; margin-top: 10px;">
                            {{ work_performed }}
                        </div>
                        
                        {% if issues_found %}
                        <p style="margin: 15px 0 5px 0;"><strong>Issues Found:</strong></p>
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 3px; border-left: 3px solid #ffc107;">
                            {{ issues_found }}
                        </div>
                        {% endif %}
                    </div>
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">Ontech ICT Management System</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_license_expiry_template(self) -> str:
        """License expiry alert template"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>License Expiry Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #dc3545; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">⚠️ License Expiry Alert</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #dc3545; margin-top: 0;">License Expiry Warning</h2>
                    <p style="font-size: 16px; line-height: 1.5;">
                        <strong>{{ total_licenses }} software license(s) will expire in {{ days_until_expiry }} day(s).</strong>
                    </p>
                    
                    <div style="background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #721c24;">Expiring Licenses</h3>
                        {% for license in licenses %}
                        <div style="margin-bottom: 20px; padding: 15px; background-color: white; border-radius: 5px; border: 1px solid #f5c6cb;">
                            <h4 style="margin: 0 0 10px 0; color: #dc3545;">{{ license.software_name }}</h4>
                            <p style="margin: 5px 0;"><strong>Vendor:</strong> {{ license.vendor }}</p>
                            <p style="margin: 5px 0;"><strong>License Type:</strong> {{ license.license_type }}</p>
                            <p style="margin: 5px 0;"><strong>Expiry Date:</strong> {{ license.expiry_date }}</p>
                            <p style="margin: 5px 0;"><strong>Total Licenses:</strong> {{ license.total_licenses }}</p>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <h4 style="margin-top: 0; color: #856404;">🚨 Action Required</h4>
                        <p style="margin-bottom: 0; color: #856404;">
                            Please review these licenses and initiate renewal processes as necessary to avoid service disruption.
                        </p>
                    </div>
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">Ontech ICT Management System</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_default_template(self) -> str:
        """Default email template with modern design"""
        return '''
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>System Notification</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;">
                <div style="background-color: #2c5aa0; color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Ontech ICT Management</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">System Notification</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #2c5aa0; margin-top: 0;">System Notification</h2>
                    <p style="font-size: 16px; line-height: 1.5;">
                        This is an automated notification from the Ontech ICT Management System.
                    </p>
                    
                    <div style="background-color: #f8f9fa; border-left: 5px solid #6c757d; padding: 20px; margin: 25px 0; border-radius: 5px;">
                        <p style="margin: 0; color: #495057;">
                            If you received this email and it was not intended for you, please contact the IT Support team.
                        </p>
                    </div>
                </div>
                
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">
                        This is an automated message from Ontech ICT Management System
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">
                        Please do not reply to this email - no_reply@ontech.co.zm
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''


# Create global email service instance
email_service = EmailService()


# ==========================================================================
# INTEGRATION FUNCTION FOR FLASK APP
# ==========================================================================

def init_email_service(app):
    """Initialize email service with Flask app"""
    email_service.init_app(app)
    return email_service