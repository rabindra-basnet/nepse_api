import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, date
import requests
from wasmtime import Store, Module, Instance

from nepse_scraper import TokenParser, PayloadParser, Nepse, Nepse_scraper

class TestTokenParser(unittest.TestCase):
    """Test cases for TokenParser class that handles WASM token parsing"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the WASM file loading since we don't have the actual file
        with patch('wasmtime.Module.from_file') as mock_module:
            with patch('wasmtime.Instance') as mock_instance:
                # Mock the WASM exports
                mock_exports = {
                    'cdx': Mock(return_value=22),
                    'rdx': Mock(return_value=32), 
                    'bdx': Mock(return_value=60),
                    'ndx': Mock(return_value=88),
                    'mdx': Mock(return_value=110)
                }
                mock_instance.return_value.exports.return_value = mock_exports
                
                # Create TokenParser instance with mocked WASM
                self.token_parser = TokenParser()
    
    def test_parse_token_response(self):
        """Test token parsing functionality"""
        # Sample token response from NEPSE API
        token_response = {
            'salt1': 123,
            'salt2': 456, 
            'salt3': 789,
            'salt4': 101,
            'salt5': 112,
            'accessToken': 'abcdefghijklmnopqrstuvwxyz1234567890',
            'refreshToken': 'zyxwvutsrqponmlkjihgfedcba0987654321'
        }
        
        # Parse tokens
        parsed_access, parsed_refresh = self.token_parser.parse_token_response(token_response)
        
        # Verify tokens are strings
        self.assertIsInstance(parsed_access, str)
        self.assertIsInstance(parsed_refresh, str)
        
        # Verify tokens are shorter than originals (characters removed)
        self.assertLess(len(parsed_access), len(token_response['accessToken']))
        self.assertLess(len(parsed_refresh), len(token_response['refreshToken']))
        
        print(f"Original access token: {token_response['accessToken']}")
        print(f"Parsed access token: {parsed_access}")
        print(f"Original refresh token: {token_response['refreshToken']}")
        print(f"Parsed refresh token: {parsed_refresh}")


class TestPayloadParser(unittest.TestCase):
    """Test cases for PayloadParser class that generates request payloads"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('requests.request') as mock_request:
            # Mock the market open API response
            mock_response = Mock()
            mock_response.content = json.dumps({"id": 15}).encode()
            mock_request.return_value = mock_response
            
            self.payload_parser = PayloadParser()
    
    @patch('requests.request')
    def test_return_payload_stock_live(self, mock_request):
        """Test payload generation for stock live data"""
        # Mock API response
        mock_response = Mock()
        mock_response.content = json.dumps({"id": 25}).encode()
        mock_request.return_value = mock_response
        
        # Mock access token
        access_token_value = ['mock_token', {'salt1': 100, 'salt2': 200, 'salt3': 300, 'salt4': 400}]
        
        # Test stock-live payload
        payload_id = self.payload_parser.return_payload(access_token_value, which='stock-live')
        
        # Verify payload is calculated correctly
        expected_base = self.payload_parser.dummyData[25] + 25 + 2 * datetime.now().day
        self.assertEqual(payload_id, expected_base)
        
        print(f"Generated stock-live payload ID: {payload_id}")
    
    @patch('requests.request')
    def test_return_payload_sector_live(self, mock_request):
        """Test payload generation for sector live data"""
        mock_response = Mock()
        mock_response.content = json.dumps({"id": 30}).encode()
        mock_request.return_value = mock_response
        
        access_token_value = ['mock_token', {'salt1': 100, 'salt2': 200, 'salt3': 300, 'salt4': 400}]
        
        payload_id = self.payload_parser.return_payload(access_token_value, which='sector-live')
        
        # Verify payload calculation includes salt values
        self.assertIsInstance(payload_id, int)
        print(f"Generated sector-live payload ID: {payload_id}")


class TestNepse(unittest.TestCase):
    """Test cases for main Nepse class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('nepse_module.PayloadParser'), patch('nepse_module.TokenParser'):
            self.nepse = Nepse()
    
    @patch('requests.request')
    def test_get_valid_token(self, mock_request):
        """Test token generation"""
        # Mock token API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'salt1': '123',
            'salt2': '456', 
            'salt3': '789',
            'salt4': '101',
            'salt5': '112',
            'accessToken': 'sample_access_token',
            'refreshToken': 'sample_refresh_token'
        }
        mock_request.return_value = mock_response
        
        # Mock token parser
        self.nepse.token_parser.parse_token_response = Mock(return_value=('parsed_access', 'parsed_refresh'))
        
        result = self.nepse.get_valid_token()
        
        # Verify token structure
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 'parsed_access')
        self.assertIsInstance(result[1], dict)
        
        print(f"Generated token: {result}")
    
    @patch('requests.request')
    def test_request_api_success(self, mock_request):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Mock payload parser
        self.nepse.parser_obj.return_payload = Mock(return_value=12345)
        
        access_token = ['test_token', {'salt1': 100}]
        
        response = self.nepse.request_api('https://test.com/api', access_token)
        
        self.assertEqual(response.status_code, 200)
        print("API request successful")
    
    def test_request_api_failure(self):
        """Test API request failure handling"""
        with patch('requests.request') as mock_request:
            # Mock failed response
            mock_request.side_effect = Exception("Network error")
            
            access_token = ['test_token', {'salt1': 100}]
            
            with self.assertRaises(ValueError) as context:
                self.nepse.request_api('https://test.com/api', access_token)
            
            self.assertIn("Error sending request", str(context.exception))
            print(f"Caught expected error: {context.exception}")


class TestNepseScraper(unittest.TestCase):
    """Test cases for Nepse_scraper class - the main interface"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('nepse_module.Nepse') as mock_nepse:
            self.scraper = Nepse_scraper()
            self.mock_nepse_obj = mock_nepse.return_value
    
    def test_is_trading_day_true(self):
        """Test when today is a trading day"""
        # Mock response for trading day
        mock_response = {
            'asOf': f'{date.today()}T10:30:00',
            'isOpen': 'OPEN'
        }
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.is_trading_day()
        self.assertTrue(result)
        print("Today is a trading day")
    
    def test_is_trading_day_false(self):
        """Test when today is not a trading day"""
        # Mock response for non-trading day
        mock_response = {
            'asOf': '2023-01-01T10:30:00',  # Different date
            'isOpen': 'CLOSED'
        }
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.is_trading_day()
        self.assertFalse(result)
        print("Today is not a trading day")
    
    def test_is_market_open_true(self):
        """Test when market is currently open"""
        mock_response = {'isOpen': 'OPEN'}
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.is_market_open()
        self.assertTrue(result)
        print("Market is currently open")
    
    def test_is_market_open_false(self):
        """Test when market is currently closed"""
        mock_response = {'isOpen': 'CLOSED'}
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.is_market_open()
        self.assertFalse(result)
        print("Market is currently closed")
    
    def test_get_today_price(self):
        """Test getting today's price data"""
        mock_response = {
            'content': [
                {
                    'symbol': 'NABIL',
                    'ltp': 1200.0,
                    'pointChange': 25.0,
                    'percentChange': 2.13
                }
            ]
        }
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.get_today_price()
        
        self.assertIn('content', result)
        self.assertIsInstance(result['content'], list)
        print(f"Today's price data: {result}")
    
    def test_get_ticker_info_single(self):
        """Test getting single ticker information"""
        # Mock security data
        self.scraper._get_security = Mock(return_value=[
            {'symbol': 'NABIL', 'id': 123}
        ])
        
        # Mock ticker info response
        mock_response = {
            'symbol': 'NABIL',
            'ltp': 1200.0,
            'volume': 1000,
            'turnover': 1200000.0
        }
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.get_ticker_info('NABIL')
        
        self.assertEqual(result['symbol'], 'NABIL')
        self.assertEqual(result['ltp'], 1200.0)
        print(f"NABIL ticker info: {result}")
    
    def test_get_ticker_info_multiple(self):
        """Test getting multiple ticker information"""
        # Mock security data
        self.scraper._get_security = Mock(return_value=[
            {'symbol': 'NABIL', 'id': 123},
            {'symbol': 'SCBL', 'id': 124}
        ])
        
        # Mock ticker info responses
        def mock_call_nepse_function(*args, **kwargs):
            if '123' in kwargs.get('url', ''):
                return {'symbol': 'NABIL', 'ltp': 1200.0}
            elif '124' in kwargs.get('url', ''):
                return {'symbol': 'SCBL', 'ltp': 800.0}
        
        self.scraper.call_nepse_function = Mock(side_effect=mock_call_nepse_function)
        
        result = self.scraper.get_ticker_info(['NABIL', 'SCBL'])
        
        self.assertIn('NABIL', result)
        self.assertIn('SCBL', result)
        self.assertEqual(result['NABIL']['ltp'], 1200.0)
        self.assertEqual(result['SCBL']['ltp'], 800.0)
        print(f"Multiple ticker info: {result}")
    
    def test_get_ticker_info_not_found(self):
        """Test error handling for non-existent ticker"""
        self.scraper._get_security = Mock(return_value=[
            {'symbol': 'NABIL', 'id': 123}
        ])
        
        with self.assertRaises(ValueError) as context:
            self.scraper.get_ticker_info('NONEXISTENT')
        
        self.assertIn("Not Found", str(context.exception))
        print(f"Caught expected error for non-existent ticker: {context.exception}")
    
    def test_get_live_indices_valid_id(self):
        """Test getting live indices with valid ID"""
        mock_response = [
            {'time': '10:30:00', 'index': 2800.50},
            {'time': '10:31:00', 'index': 2801.20}
        ]
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.get_live_indices(58)  # NEPSE Index
        
        self.assertIsInstance(result, list)
        print(f"Live indices data: {result}")
    
    def test_get_live_indices_invalid_id(self):
        """Test error handling for invalid indices ID"""
        with self.assertRaises(ValueError) as context:
            self.scraper.get_live_indices(100)  # Invalid ID
        
        self.assertIn("not valid indices ID", str(context.exception))
        print(f"Caught expected error for invalid indices ID: {context.exception}")
    
    def test_get_trading_average_valid_days(self):
        """Test getting trading average with valid parameters"""
        mock_response = {
            'content': [
                {'symbol': 'NABIL', 'average': 1150.0}
            ]
        }
        
        self.scraper.call_nepse_function = Mock(return_value=mock_response)
        
        result = self.scraper.get_trading_average(n_days=30)
        
        self.assertIn('content', result)
        print(f"30-day trading average: {result}")
    
    def test_get_trading_average_invalid_days(self):
        """Test error handling for invalid n_days parameter"""
        with self.assertRaises(ValueError) as context:
            self.scraper.get_trading_average(n_days=200)  # > 180
        
        self.assertIn("must be between 1 and 180", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.scraper.get_trading_average(n_days=0)  # < 1
        
        print("Caught expected errors for invalid n_days parameter")


class TestIntegration(unittest.TestCase):
    """Integration tests to verify the complete workflow"""
    
    @patch('requests.request')
    def test_complete_workflow(self, mock_request):
        """Test the complete workflow from token generation to data retrieval"""
        # Mock token API response
        token_response = Mock()
        token_response.json.return_value = {
            'salt1': '123', 'salt2': '456', 'salt3': '789', 'salt4': '101', 'salt5': '112',
            'accessToken': 'sample_access_token', 'refreshToken': 'sample_refresh_token'
        }
        
        # Mock data API response
        data_response = Mock()
        data_response.status_code = 200
        data_response.json.return_value = {'data': 'sample_data'}
        data_response.raise_for_status.return_value = None
        
        # Configure mock to return different responses based on URL
        def mock_request_side_effect(*args, **kwargs):
            if 'authenticate' in args[1]:  # Token URL
                return token_response
            else:  # Data URL
                return data_response
        
        mock_request.side_effect = mock_request_side_effect
        
        with patch('nepse_module.PayloadParser'), patch('nepse_module.TokenParser') as mock_token_parser:
            mock_token_parser.return_value.parse_token_response.return_value = ('parsed_token', 'parsed_refresh')
            
            scraper = Nepse_scraper()
            
            # Test that we can get data successfully
            result = scraper.get_today_market_summary()
            
            self.assertEqual(result, {'data': 'sample_data'})
            print("Complete workflow test passed")


def run_debug_tests():
    """Run specific tests to help debug the NEPSE library"""
    
    print("=" * 60)
    print("NEPSE LIBRARY DEBUG TEST SUITE")
    print("=" * 60)
    
    # Test suite for debugging specific components
    test_classes = [
        TestTokenParser,
        TestPayloadParser, 
        TestNepse,
        TestNepseScraper,
        TestIntegration
    ]
    
    for test_class in test_classes:
        print(f"\n{'='*20} {test_class.__name__} {'='*20}")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.failures:
            print(f"\nFAILURES in {test_class.__name__}:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print(f"\nERRORS in {test_class.__name__}:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")


def debug_wasm_functions():
    """Debug the WASM functions to understand their behavior"""
    
    print("\n" + "="*60)
    print("WASM FUNCTION ANALYSIS")
    print("="*60)
    
    # Analyze the WASM module structure
    print("WASM Functions found:")
    functions = ['cdx', 'rdx', 'bdx', 'ndx', 'mdx']
    
    for func in functions:
        print(f"- {func}: Takes 5 parameters (salt values), returns integer")
    
    # The data section contains lookup values
    print("\nWASM Data Section Analysis:")
    print("- Contains 40 4-byte integers (160 bytes total)")
    print("- Used as lookup table at memory address 1024")
    print("- Values range from 3 to 9")
    
    # Function behavior analysis
    print("\nFunction Behavior Analysis:")
    print("cdx/rdx: Processes digit extraction and lookup")
    print("- Extracts hundreds, tens, ones digits")
    print("- Sums specific digit combinations") 
    print("- Adds lookup table value and constant offset")
    
    print("\nPayload ID Generation Logic:")
    print("1. Get base ID from market API")
    print("2. Add dummy data value based on ID")
    print("3. Add current day * 2")
    print("4. For non-stock data: apply salt-based calculation")


if __name__ == '__main__':
    # Run the debug test suite
    run_debug_tests()
    
    # Analyze WASM functions
    debug_wasm_functions()
    
    print("\n" + "="*60)
    print("DEBUG SUMMARY")
    print("="*60)
    print("""
    Your NEPSE library does the following:

    1. TOKEN AUTHENTICATION:
       - Calls NEPSE auth API to get encrypted tokens
       - Uses WASM functions to decrypt/parse tokens
       - Tokens are required for all data requests

    2. PAYLOAD GENERATION:
       - Generates dynamic payload IDs for each request
       - Based on current date, API response, and salt values
       - Different calculations for different data types

    3. DATA SCRAPING:
       - Provides methods for all major NEPSE endpoints
       - Handles authentication automatically
       - Includes retry logic for failed requests

    4. KEY METHODS:
       - is_trading_day(): Check if market is open today
       - get_today_price(): Get current stock prices
       - get_ticker_info(): Get specific stock details
       - get_live_indices(): Get real-time index data
       - get_market_summary(): Get overall market stats

    5. DEBUGGING TIPS:
       - Check token generation first
       - Verify payload calculation logic
       - Monitor API response status codes
       - Test with known valid ticker symbols
    """)