# app/services/cgrate_service.py - cGrate SOAP Web Service Integration
import os
import xml.etree.ElementTree as ET
import requests
import secrets
import uuid
import hashlib
from datetime import datetime
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class CgrateService:
    """cGrate SOAP Web Service Integration for REA Payments"""
    
    def __init__(self):
        # Load configuration from environment
        self.wsdl_url = os.environ.get('CGRATE_WSDL_URL', 'https://543.cgrate.co.zm/Konik/KonikWs?wsdl')
        self.soap_url = os.environ.get('CGRATE_SOAP_URL', 'https://543.cgrate.co.zm/Konik/KonikWs')
        self.username = os.environ.get('CGRATE_USERNAME', '1751463093895')
        self.password = os.environ.get('CGRATE_PASSWORD', 'D6cQ21d0')
        self.timeout = int(os.environ.get('CGRATE_TIMEOUT', 30))
        self.retry_attempts = int(os.environ.get('CGRATE_RETRY_ATTEMPTS', 3))
        
        # Mock mode for testing
        self.use_mock = os.environ.get('CGRATE_MOCK_MODE', 'False').lower() == 'true'
        
        logger.info(f"cGrate service initialized - Mock mode: {self.use_mock}")
    
    def health_check(self):
        """Check if cGrate service is available"""
        if self.use_mock:
            logger.info("cGrate mock service health check: OK")
            return {'status': 'healthy', 'service': 'mock'}
        
        try:
            response = requests.get(self.wsdl_url, timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'service': 'production', 'code': response.status_code}
            else:
                return {'status': 'unhealthy', 'code': response.status_code}
        except Exception as e:
            logger.warning(f"cGrate health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _create_soap_envelope(self, body_content):
        """Create SOAP envelope with WS-Security header"""
        soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                  xmlns:kon="http://konik.cgrate.com">
    <soapenv:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" 
                       soapenv:mustUnderstand="1">
            <wsse:UsernameToken xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" 
                               wsu:Id="{self.username}">
                <wsse:Username>{self.username}</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        {body_content}
    </soapenv:Body>
</soapenv:Envelope>"""
        return soap_envelope
    
    def _make_soap_request(self, soap_body):
        """Make SOAP request to cGrate service"""
        if self.use_mock:
            return self._mock_soap_response(soap_body)
        
        soap_envelope = self._create_soap_envelope(soap_body)
        
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        try:
            response = requests.post(
                self.soap_url,
                data=soap_envelope,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return self._parse_soap_response(response.text)
            else:
                logger.error(f"SOAP request failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'SOAP request failed with status {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"SOAP request error: {e}")
            return {
                'success': False,
                'error': f'SOAP request error: {str(e)}'
            }
    
    def _parse_soap_response(self, soap_response):
        """Parse SOAP response XML"""
        try:
            # Remove namespaces for easier parsing
            clean_xml = soap_response.replace('env:', '').replace('ns2:', '')
            
            root = ET.fromstring(clean_xml)
            
            # Look for return element in response
            return_elem = root.find('.//return')
            if return_elem is not None:
                response_data = {}
                
                for child in return_elem:
                    tag = child.tag
                    text = child.text or ''
                    response_data[tag] = text
                
                # Check response code
                response_code = response_data.get('responseCode', '1')
                if response_code == '0':
                    return {
                        'success': True,
                        'data': response_data
                    }
                else:
                    return {
                        'success': False,
                        'error': response_data.get('responseMessage', 'Unknown error'),
                        'data': response_data
                    }
            else:
                logger.error(f"No return element found in SOAP response: {soap_response}")
                return {
                    'success': False,
                    'error': 'Invalid SOAP response format'
                }
                
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return {
                'success': False,
                'error': f'XML parse error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return {
                'success': False,
                'error': f'Response parsing error: {str(e)}'
            }
    
    def get_account_balance(self):
        """Get cGrate account balance"""
        soap_body = "<kon:getAccountBalance/>"
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            try:
                balance = float(data.get('accountBalance', 0))
                return {
                    'success': True,
                    'balance': balance,
                    'currency': 'ZMW',
                    'message': data.get('responseMessage', 'Balance retrieved successfully')
                }
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': 'Invalid balance format in response'
                }
        else:
            return result
    
    def process_customer_payment(self, customer_phone, amount, payment_reference=None):
        """Process customer payment through cGrate"""
        if not payment_reference:
            payment_reference = self.generate_payment_reference()
        
        # Validate and format phone number
        formatted_phone = self.format_phone_number(customer_phone)
        if not formatted_phone:
            return {
                'success': False,
                'error': 'Invalid phone number format'
            }
        
        soap_body = f"""<kon:processCustomerPayment>
            <transactionAmount>{amount}</transactionAmount>
            <customerMobile>{formatted_phone}</customerMobile>
            <paymentReference>{payment_reference}</paymentReference>
        </kon:processCustomerPayment>"""
        
        logger.info(f"Processing customer payment - Phone: {formatted_phone}, Amount: {amount}, Ref: {payment_reference}")
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            return {
                'success': True,
                'data': {
                    'payment_id': data.get('paymentID'),
                    'payment_reference': payment_reference,
                    'amount': str(amount),
                    'currency': 'ZMW',
                    'customer_phone': formatted_phone,
                    'status': 'PENDING'
                },
                'message': data.get('responseMessage', 'Payment initiated successfully')
            }
        else:
            return result
    
    def query_customer_payment(self, payment_reference):
        """Query customer payment status"""
        soap_body = f"""<kon:queryCustomerPayment>
            <paymentReference>{payment_reference}</paymentReference>
        </kon:queryCustomerPayment>"""
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            
            # Map cGrate status to standard status
            cgrate_status = data.get('paymentStatus', 'UNKNOWN').upper()
            
            if cgrate_status in ['SUCCESSFUL', 'SUCCESS', 'COMPLETED']:
                status = 'SUCCESSFUL'
            elif cgrate_status in ['FAILED', 'FAILURE', 'ERROR']:
                status = 'FAILED'
            elif cgrate_status in ['PENDING', 'PROCESSING']:
                status = 'PENDING'
            else:
                status = 'UNKNOWN'
            
            return {
                'success': True,
                'status': status,
                'data': data,
                'payment_reference': payment_reference
            }
        else:
            return result
    
    def purchase_electricity_token(self, meter_number, amount, transaction_reference=None):
        """Purchase Zesco electricity token"""
        if not transaction_reference:
            transaction_reference = str(uuid.uuid4())
        
        soap_body = f"""<kon:purchaseZescoVoucher>
            <Voucher>
                <isFixed>false</isFixed>
                <receipient>{meter_number}</receipient>
                <serviceProvider>Zesco</serviceProvider>
                <transactionReference>{transaction_reference}</transactionReference>
                <voucherType>Token</voucherType>
                <voucherValue>{amount}</voucherValue>
            </Voucher>
        </kon:purchaseZescoVoucher>"""
        
        logger.info(f"Purchasing electricity token - Meter: {meter_number}, Amount: {amount}")
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            return {
                'success': True,
                'data': {
                    'transaction_reference': transaction_reference,
                    'meter_number': meter_number,
                    'amount': str(amount),
                    'currency': 'ZMW',
                    'electricity_token': data.get('voucherPins', ''),
                    'units_purchased': self._calculate_units_from_amount(amount),
                    'voucher_serial': data.get('voucherSerial', ''),
                    'receipt_number': data.get('receiptNumber', '')
                },
                'message': data.get('responseMessage', 'Token purchased successfully')
            }
        else:
            return result
    
    def get_customer_by_meter(self, meter_number):
        """Get customer name by meter number"""
        soap_body = f"""<kon:getBillCustomerName>
            <serviceProvider>Zesco</serviceProvider>
            <billPaymentAccountNumber>{meter_number}</billPaymentAccountNumber>
        </kon:getBillCustomerName>"""
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            customer_name = data.get('billCustomerName', '').replace('N:', '')
            
            return {
                'success': True,
                'customer': {
                    'name': customer_name.strip(),
                    'meter_number': meter_number,
                    'service_provider': 'Zesco'
                }
            }
        else:
            return result
    
    def query_transaction_status(self, transaction_reference):
        """Query transaction status"""
        soap_body = f"""<kon:queryTransactionStatus>
            <transactionReference>{transaction_reference}</transactionReference>
        </kon:queryTransactionStatus>"""
        
        result = self._make_soap_request(soap_body)
        
        if result['success']:
            data = result.get('data', {})
            
            # Map transaction status
            transaction_status = data.get('transactionStatus', 'UNKNOWN').upper()
            
            if transaction_status in ['SUCCESSFUL', 'SUCCESS', 'COMPLETED']:
                status = 'SUCCESSFUL'
            elif transaction_status in ['FAILED', 'FAILURE', 'ERROR']:
                status = 'FAILED'
            elif transaction_status in ['PENDING', 'PROCESSING']:
                status = 'PENDING'
            else:
                status = 'UNKNOWN'
            
            return {
                'success': True,
                'status': status,
                'data': data,
                'transaction_reference': transaction_reference
            }
        else:
            return result
    
    def initiate_payment(self, order_number, amount, description, phone_number, callback_url=None, **kwargs):
        """
        Main payment initiation method - compatible with GeePay interface
        This method provides compatibility with existing GeePay integration
        """
        logger.info(f"Initiating cGrate payment - Order: {order_number}, Amount: {amount}, Phone: {phone_number}")
        
        # Step 1: Process customer payment to get payment ID
        payment_result = self.process_customer_payment(phone_number, amount, order_number)
        
        if not payment_result['success']:
            return payment_result
        
        payment_data = payment_result['data']
        payment_id = payment_data.get('payment_id')
        
        # Return in GeePay-compatible format
        return {
            'success': True,
            'data': {
                'geepayref': payment_id,  # Use payment_id as geepayref for compatibility
                'mtnref': f"cgrate_{order_number}",
                'transaction_id': order_number,
                'amount': str(amount),
                'currency': 'ZMW',
                'payerphone': phone_number,
                'ordernumber': order_number,
                'status': 'PENDING'
            },
            'message': payment_result.get('message', 'Payment initiated successfully'),
            'transaction_ref': order_number
        }
    
    def check_payment_status(self, transaction_id):
        """
        Check payment status - compatible with GeePay interface
        """
        logger.info(f"Checking cGrate payment status for: {transaction_id}")
        
        # Query payment status
        status_result = self.query_customer_payment(transaction_id)
        
        if status_result['success']:
            return {
                'success': True,
                'status': status_result['status'],
                'data': status_result['data'],
                'transaction_id': transaction_id
            }
        else:
            return status_result
    
    def format_phone_number(self, phone_number):
        """Format phone number to Zambian format"""
        if not phone_number:
            return None
        
        import re
        phone = re.sub(r'[^\d]', '', phone_number)
        
        # Remove leading zeros and country code variations
        if phone.startswith('260'):
            if len(phone) == 12:
                return phone
        elif phone.startswith('0'):
            if len(phone) == 10:
                return '260' + phone[1:]
        elif len(phone) == 9 and phone[0] in ['9', '7']:
            return '260' + phone
        
        return None
    
    def validate_phone_number(self, phone_number, network=None):
        """Validate Zambian phone number"""
        formatted = self.format_phone_number(phone_number)
        if not formatted:
            return False
        
        # Check if it's a valid Zambian mobile number
        prefixes = ['96', '97', '95', '76', '77', '94']
        return formatted[3:5] in prefixes
    
    def get_network_from_phone(self, phone_number):
        """Determine network from phone number"""
        formatted = self.format_phone_number(phone_number)
        if not formatted:
            return None
        
        prefix = formatted[3:5]
        if prefix in ['96', '97']:
            return 'MTN'
        elif prefix in ['95', '76', '77']:
            return 'AIRTEL'
        elif prefix in ['94']:
            return 'ZAMTEL'
        return None
    
    def get_payment_limits(self):
        """Get payment limits"""
        return {
            'min_amount': 5.00,
            'max_amount': 50000.00,
            'currency': 'ZMW'
        }
    
    def get_supported_networks(self):
        """Get supported networks"""
        return ['MTN', 'AIRTEL', 'ZAMTEL']
    
    def generate_payment_reference(self, prefix="REA"):
        """Generate unique payment reference"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(4).upper()
        return f"{prefix}{timestamp}{random_part}"
    
    def generate_order_number(self, prefix="REA"):
        """Generate unique order number - compatible with GeePay interface"""
        return self.generate_payment_reference(prefix)
    
    def _calculate_units_from_amount(self, amount):
        """Calculate electricity units from amount (using demo rate)"""
        # Demo calculation: 2.5 kWh per ZMW
        return round(float(amount) * 2.5, 2)
    
    def _mock_soap_response(self, soap_body):
        """Generate mock SOAP response for testing"""
        logger.info(f"Mock cGrate SOAP request: {soap_body}")
        
        import time
        time.sleep(0.5)  # Simulate network delay
        
        if 'processCustomerPayment' in soap_body:
            payment_id = f"CGRATE{secrets.token_hex(6).upper()}"
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': 'Mock payment initiated successfully',
                    'paymentID': payment_id
                }
            }
        
        elif 'queryCustomerPayment' in soap_body:
            # Simulate random payment status for testing
            statuses = ['SUCCESSFUL', 'PENDING', 'FAILED']
            import random
            status = random.choice(statuses)
            
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': f'Mock payment status: {status}',
                    'paymentStatus': status
                }
            }
        
        elif 'purchaseZescoVoucher' in soap_body:
            mock_token = f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
            
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': 'Mock token purchased successfully',
                    'voucherPins': mock_token,
                    'voucherSerial': f"MOCK{secrets.token_hex(4)}",
                    'receiptNumber': f"RCP{secrets.token_hex(6)}"
                }
            }
        
        elif 'getBillCustomerName' in soap_body:
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': 'Mock customer found',
                    'billCustomerName': 'N:MOCK CUSTOMER NAME'
                }
            }
        
        elif 'getAccountBalance' in soap_body:
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': 'Mock account balance retrieved',
                    'accountBalance': '1000.50'
                }
            }
        
        else:
            return {
                'success': True,
                'data': {
                    'responseCode': '0',
                    'responseMessage': 'Mock operation successful'
                }
            }

# Compatibility alias
GeepayService = CgrateService