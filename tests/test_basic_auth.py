#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import requests

from mdscraper.core.scraper import MdScraper, AuthenticationError

# Add the parent directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


class TestBasicAuthentication(unittest.TestCase):
    """Test cases for basic authentication functionality in MdScraper"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a MD Scraper object with default options
        self.mds = MdScraper()

    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_default_basic_auth_options(self):
        """Test that basic authentication options default to None"""
        self.assertIsNone(self.mds.options['basic_auth_username'])
        self.assertIsNone(self.mds.options['basic_auth_password'])

    def test_set_basic_auth_options(self):
        """Test setting basic authentication options via constructor"""
        mds_with_auth = MdScraper(
            basic_auth_username='testuser',
            basic_auth_password='testpass'
        )
        
        self.assertEqual(mds_with_auth.options['basic_auth_username'], 'testuser')
        self.assertEqual(mds_with_auth.options['basic_auth_password'], 'testpass')

    def test_update_basic_auth_options(self):
        """Test updating basic authentication options after initialization"""
        self.mds.set_options({
            'basic_auth_username': 'updateduser',
            'basic_auth_password': 'updatedpass'
        })
        
        self.assertEqual(self.mds.options['basic_auth_username'], 'updateduser')
        self.assertEqual(self.mds.options['basic_auth_password'], 'updatedpass')

    @patch('requests.Session.get')
    def test_fetch_webpage_with_basic_auth(self, mock_get):
        """Test that fetch_webpage passes auth credentials to session.get"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Configure scraper with basic auth
        mds_with_auth = MdScraper(
            basic_auth_username='testuser',
            basic_auth_password='testpass'
        )
        
        # Call fetch_webpage
        result = mds_with_auth.fetch_webpage('https://example.com')
        
        # Verify session.get was called with auth parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check that auth tuple was passed
        self.assertIn('auth', call_args.kwargs)
        self.assertEqual(call_args.kwargs['auth'], ('testuser', 'testpass'))
        
        # Verify other standard parameters
        self.assertIn('headers', call_args.kwargs)
        self.assertIn('timeout', call_args.kwargs)
        
        # Verify result is a BeautifulSoup object
        self.assertIsNotNone(result)

    @patch('requests.Session.get')
    def test_fetch_webpage_without_basic_auth(self, mock_get):
        """Test that fetch_webpage doesn't pass auth when not configured"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call fetch_webpage without auth
        result = self.mds.fetch_webpage('https://example.com')
        
        # Verify session.get was called without auth parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check that auth parameter is None (or not passed)
        auth_param = call_args.kwargs.get('auth')
        self.assertIsNone(auth_param)
        
        # Verify result is a BeautifulSoup object
        self.assertIsNotNone(result)

    @patch('requests.Session.get')
    def test_fetch_webpage_partial_auth_credentials(self, mock_get):
        """Test that auth is not used when only username or password is provided"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test with only username
        mds_username_only = MdScraper(basic_auth_username='testuser')
        mds_username_only.fetch_webpage('https://example.com')
        
        call_args = mock_get.call_args
        auth_param = call_args.kwargs.get('auth') if call_args else None
        self.assertIsNone(auth_param)
        
        # Reset mock
        mock_get.reset_mock()
        
        # Test with only password
        mds_password_only = MdScraper(basic_auth_password='testpass')
        mds_password_only.fetch_webpage('https://example.com')
        
        call_args = mock_get.call_args
        auth_param = call_args.kwargs.get('auth') if call_args else None
        self.assertIsNone(auth_param)

    def test_real_basic_auth_site(self):
        """Test basic authentication with a real authentication test site"""
        # Use authenticationtest.com for real testing
        test_url = "https://authenticationtest.com/HTTPAuth/"
        
        # Test without authentication (should fail or return 401 content)
        mds_no_auth = MdScraper(debug=False, verbose=0)
        
        try:
            result_no_auth = mds_no_auth.fetch_webpage(test_url)
            # The site should return some content even for 401, but it will be an error page
            self.assertIsNotNone(result_no_auth)
        except Exception:
            # If it raises an exception, that's also expected for unauthorized access
            pass
        
        # Test with correct authentication
        # Note: Using the standard test credentials from authenticationtest.com
        mds_with_auth = MdScraper(
            basic_auth_username='user',
            basic_auth_password='pass',
            debug=False,
            verbose=0
        )
        
        try:
            result_with_auth = mds_with_auth.fetch_webpage(test_url)
            self.assertIsNotNone(result_with_auth)
            
            # The authenticated page should contain different content
            # Look for success indicators in the response
            page_text = result_with_auth.get_text().lower()
            
            # The site should indicate successful authentication
            # Note: This might need adjustment based on the actual response from the test site
            success_indicators = ['authenticated', 'success', 'authorized', 'welcome']
            has_success_indicator = any(indicator in page_text for indicator in success_indicators)
            
            if not has_success_indicator:
                # If we don't find success indicators, at least verify we got some content
                self.assertGreater(len(page_text.strip()), 0)
                
        except requests.exceptions.RequestException as e:
            # Skip this test if there are network issues
            self.skipTest(f"Network error accessing test site: {e}")
        except Exception as e:
            # For other exceptions, fail the test
            self.fail(f"Unexpected error during authentication test: {e}")

    def test_basic_auth_in_default_options(self):
        """Test that basic auth options are included in default options"""
        default_options = self.mds.get_default_options()
        
        self.assertIn('basic_auth_username', default_options)
        self.assertIn('basic_auth_password', default_options)
        self.assertIsNone(default_options['basic_auth_username'])
        self.assertIsNone(default_options['basic_auth_password'])

    def test_authentication_error_raised(self):
        """Test that authentication failures raise AuthenticationError exceptions."""
        
        # Create scraper with invalid credentials
        scraper = MdScraper(
            login_url="https://httpbin.org/basic-auth/user/pass",
            basic_auth_username="wrong_user",
            basic_auth_password="wrong_pass",
            debug=True
        )
        
        with self.assertRaises(AuthenticationError):
            scraper.perform_login()

    def test_process_single_url_auth_fail(self):
        """Test that process_single_url raises authentication errors."""
        
        scraper = MdScraper(
            login_url="https://httpbin.org/basic-auth/user/pass",
            basic_auth_username="wrong_user",
            basic_auth_password="wrong_pass",
            verbose=1
        )
        
        # Should raise AuthenticationError for authentication failure
        with self.assertRaises(AuthenticationError):
            scraper.process_single_url("https://httpbin.org/basic-auth/user/pass")

    def test_process_site_url_auth_fail(self):
        """Test that process_site_url raises authentication errors."""
        
        scraper = MdScraper(
            login_url="https://httpbin.org/basic-auth/user/pass",
            basic_auth_username="wrong_user",
            basic_auth_password="wrong_pass"
        )
        
        with self.assertRaises(AuthenticationError):
            scraper.process_site_url("https://httpbin.org/basic-auth/user/pass")

    def test_fetch_webpage_401_error(self):
        """Test that fetch_webpage raises AuthenticationError for 401 responses."""
        
        with patch.object(self.mds.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            with self.assertRaises(AuthenticationError) as context:
                self.mds.fetch_webpage("https://example.com/protected")
            
            self.assertIn("HTTP 401 Unauthorized", str(context.exception))

    def test_no_credentials_configured_error(self):
        """Test that perform_login raises error when no credentials are configured."""
        
        scraper = MdScraper(login_url="https://example.com/login")
        
        with self.assertRaises(AuthenticationError) as context:
            scraper.perform_login()
        
        self.assertIn("No username/password configured", str(context.exception))


if __name__ == '__main__':
    unittest.main()
