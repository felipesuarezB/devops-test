#!/usr/bin/env python3
"""
Simple API tests for the blacklist microservice
"""
import sys
import os
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.blacklist import BlacklistEntry

class BlacklistAPITestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
        # Get auth token
        auth_response = self.client.post('/auth/token', 
                                       json={'client_id': 'test-client'})
        self.token = json.loads(auth_response.data)['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_auth_token_generation(self):
        """Test JWT token generation"""
        response = self.client.post('/auth/token', 
                                  json={'client_id': 'test-client'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('token_type', data)
        self.assertEqual(data['token_type'], 'Bearer')
    
    def test_add_email_to_blacklist(self):
        """Test adding email to blacklist"""
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Test reason'
        }
        
        response = self.client.post('/blacklists', 
                                  json=payload, 
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'test@example.com')
        self.assertIn('message', data)
    
    def test_add_duplicate_email(self):
        """Test adding duplicate email returns 409"""
        payload = {
            'email': 'duplicate@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Test reason'
        }
        
        # Add first time
        self.client.post('/blacklists', json=payload, headers=self.headers)
        
        # Try to add again
        response = self.client.post('/blacklists', 
                                  json=payload, 
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 409)
    
    def test_check_blacklisted_email(self):
        """Test checking if email is blacklisted"""
        # First add an email
        payload = {
            'email': 'blacklisted@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Spam'
        }
        self.client.post('/blacklists', json=payload, headers=self.headers)
        
        # Check if it's blacklisted
        response = self.client.get('/blacklists/blacklisted@example.com',
                                 headers=self.headers)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['is_blacklisted'])
        self.assertEqual(data['blocked_reason'], 'Spam')
    
    def test_check_non_blacklisted_email(self):
        """Test checking non-blacklisted email"""
        response = self.client.get('/blacklists/clean@example.com',
                                 headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['is_blacklisted'])
        self.assertIsNone(data['blocked_reason'])
    
    def test_invalid_email_format(self):
        """Test invalid email format returns 400"""
        payload = {
            'email': 'invalid-email',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        
        response = self.client.post('/blacklists', 
                                  json=payload, 
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_uuid_format(self):
        """Test invalid UUID format returns 400"""
        payload = {
            'email': 'test@example.com',
            'app_uuid': 'invalid-uuid'
        }
        
        response = self.client.post('/blacklists', 
                                  json=payload, 
                                  headers=self.headers)
        
        self.assertEqual(response.status_code, 400)
    
    def test_unauthorized_access(self):
        """Test unauthorized access returns 401"""
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        
        response = self.client.post('/blacklists', json=payload)
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
