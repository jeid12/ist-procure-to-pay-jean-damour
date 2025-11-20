"""
Test script to verify the P2P backend is working correctly.
Run this after starting the server to test basic functionality.
"""

import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def print_status(message, success=True):
    symbol = "✓" if success else "✗"
    print(f"{symbol} {message}")

def test_server_running():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/docs/", timeout=5)
        if response.status_code == 200:
            print_status("Server is running")
            return True
        else:
            print_status(f"Server returned status {response.status_code}", False)
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Server is not running: {e}", False)
        return False

def test_user_registration():
    """Test user registration"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json={
                "email": f"testuser{int(time.time())}@example.com",
                "password": "test123456",
                "password2": "test123456",
                "first_name": "Test",
                "last_name": "User",
                "role": "staff"
            }
        )
        if response.status_code == 201:
            print_status("User registration works")
            return True, response.json()
        else:
            print_status(f"Registration failed: {response.json()}", False)
            return False, None
    except Exception as e:
        print_status(f"Registration error: {e}", False)
        return False, None

def test_user_login():
    """Test user login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={
                "email": "staff@test.com",
                "password": "test123"
            }
        )
        if response.status_code == 200:
            data = response.json()
            if "access" in data and "refresh" in data:
                print_status("User login works")
                return True, data["access"]
            else:
                print_status("Login response missing tokens", False)
                return False, None
        else:
            print_status(f"Login failed: {response.json()}", False)
            return False, None
    except Exception as e:
        print_status(f"Login error: {e}", False)
        return False, None

def test_create_request(token):
    """Test creating purchase request"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/p2p/requests/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Purchase Request",
                "description": "Testing the API",
                "amount": "1000.00",
                "items": [
                    {
                        "item_name": "Test Item",
                        "description": "Test item description",
                        "quantity": 1,
                        "unit_price": "1000.00"
                    }
                ]
            }
        )
        if response.status_code == 201:
            data = response.json()
            print_status("Purchase request creation works")
            return True, data["id"]
        else:
            print_status(f"Request creation failed: {response.json()}", False)
            return False, None
    except Exception as e:
        print_status(f"Request creation error: {e}", False)
        return False, None

def test_view_requests(token):
    """Test viewing purchase requests"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/p2p/requests/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print_status(f"Purchase request listing works ({data['count']} requests)")
            return True
        else:
            print_status(f"Request listing failed: {response.status_code}", False)
            return False
    except Exception as e:
        print_status(f"Request listing error: {e}", False)
        return False

def test_approval_workflow(request_id):
    """Test the approval workflow"""
    # Login as approver1
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={"email": "approver1@test.com", "password": "test123"}
        )
        if response.status_code != 200:
            print_status("Approver1 login failed", False)
            return False
        
        approver1_token = response.json()["access"]
        
        # Approve at level 1
        response = requests.post(
            f"{BASE_URL}/api/p2p/requests/{request_id}/approve/",
            headers={"Authorization": f"Bearer {approver1_token}"},
            json={"comments": "Test approval L1"}
        )
        if response.status_code != 200:
            print_status(f"Level 1 approval failed: {response.json()}", False)
            return False
        
        print_status("Level 1 approval works")
        
        # Login as approver2
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={"email": "approver2@test.com", "password": "test123"}
        )
        if response.status_code != 200:
            print_status("Approver2 login failed", False)
            return False
        
        approver2_token = response.json()["access"]
        
        # Approve at level 2
        response = requests.post(
            f"{BASE_URL}/api/p2p/requests/{request_id}/approve/",
            headers={"Authorization": f"Bearer {approver2_token}"},
            json={"comments": "Test approval L2"}
        )
        if response.status_code != 200:
            print_status(f"Level 2 approval failed: {response.json()}", False)
            return False
        
        print_status("Level 2 approval works")
        print_status("Purchase Order should be generated")
        
        return True
        
    except Exception as e:
        print_status(f"Approval workflow error: {e}", False)
        return False

def test_view_purchase_orders():
    """Test viewing purchase orders as finance"""
    try:
        # Login as finance
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={"email": "finance@test.com", "password": "test123"}
        )
        if response.status_code != 200:
            print_status("Finance login failed", False)
            return False
        
        finance_token = response.json()["access"]
        
        # View purchase orders
        response = requests.get(
            f"{BASE_URL}/api/p2p/orders/",
            headers={"Authorization": f"Bearer {finance_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print_status(f"Purchase order viewing works ({data['count']} POs)")
            return True
        else:
            print_status(f"PO viewing failed: {response.status_code}", False)
            return False
            
    except Exception as e:
        print_status(f"PO viewing error: {e}", False)
        return False

def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("P2P Backend Test Suite")
    print("="*60 + "\n")
    
    # Test 1: Server running
    print("1. Testing server availability...")
    if not test_server_running():
        print("\n❌ Server is not running. Please start it with:")
        print("   docker-compose up")
        sys.exit(1)
    
    # Test 2: User registration
    print("\n2. Testing user registration...")
    success, user_data = test_user_registration()
    
    # Test 3: User login
    print("\n3. Testing user login...")
    success, token = test_user_login()
    if not success:
        print("\n❌ Login failed. Make sure test data is created with:")
        print("   docker-compose exec web python manage.py seed_data")
        sys.exit(1)
    
    # Test 4: View requests
    print("\n4. Testing request listing...")
    test_view_requests(token)
    
    # Test 5: Create request
    print("\n5. Testing request creation...")
    success, request_id = test_create_request(token)
    
    if success and request_id:
        # Test 6: Approval workflow
        print("\n6. Testing approval workflow...")
        test_approval_workflow(request_id)
        
        # Test 7: View purchase orders
        print("\n7. Testing purchase order viewing...")
        test_view_purchase_orders()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. View API docs: http://localhost:8000/api/docs/")
    print("2. Access admin: http://localhost:8000/admin/")
    print("3. Import Postman collection for full API testing")
    print("\n")

if __name__ == "__main__":
    run_tests()
