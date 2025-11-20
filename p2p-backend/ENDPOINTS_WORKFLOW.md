# Endpoints Workflow Guide

This document provides a step-by-step guide to manually test and understand the workflow of the endpoints in the procure-to-pay system. It explains the purpose of each endpoint, who can access it, when to use it, and what data to provide.

---

## 1. Authentication Endpoints

### **1.1 Register**
- **URL**: `/api/auth/register/`
- **Method**: POST
- **Who**: Any new user.
- **When**: To create a new account.
- **What to Provide**:
  ```json
  {
    "username": "new_user",
    "password": "secure_password",
    "email": "user@example.com"
  }
  ```
- **Response**: Returns the created user details.

### **1.2 Login**
- **URL**: `/api/auth/login/`
- **Method**: POST
- **Who**: Registered users.
- **When**: To obtain an access token.
- **What to Provide**:
  ```json
  {
    "username": "existing_user",
    "password": "secure_password"
  }
  ```
- **Response**: Returns an access token and refresh token.

### **1.3 Refresh Token**
- **URL**: `/api/auth/token/refresh/`
- **Method**: POST
- **Who**: Logged-in users.
- **When**: To refresh the access token.
- **What to Provide**:
  ```json
  {
    "refresh": "<refresh_token>"
  }
  ```
- **Response**: Returns a new access token.

---

## 2. Purchase Request Endpoints

### **2.1 Create Purchase Request**
- **URL**: `/api/p2p/requests/`
- **Method**: POST
- **Who**: Staff users.
- **When**: To create a new purchase request.
- **What to Provide**:
  ```json
  {
    "title": "Office Supplies",
    "description": "Request for office supplies",
    "amount": 500.00
  }
  ```
- **Response**: Returns the created purchase request details.

### **2.2 View All Requests**
- **URL**: `/api/p2p/requests/`
- **Method**: GET
- **Who**: Staff and approvers.
- **When**: To view all purchase requests.
- **What to Provide**: None.
- **Response**: Returns a list of purchase requests.

### **2.3 Approve Request**
- **URL**: `/api/p2p/requests/<request_id>/approve/`
- **Method**: POST
- **Who**: Approvers.
- **When**: To approve a purchase request.
- **What to Provide**: None.
- **Response**: Returns the updated request details.

### **2.4 Reject Request**
- **URL**: `/api/p2p/requests/<request_id>/reject/`
- **Method**: POST
- **Who**: Approvers.
- **When**: To reject a purchase request.
- **What to Provide**: None.
- **Response**: Returns the updated request details.

---

## 3. File Upload Endpoints

### **3.1 Upload Proforma Invoice**
- **URL**: `/api/p2p/requests/<request_id>/upload_proforma/`
- **Method**: POST
- **Who**: Staff users.
- **When**: To upload a proforma invoice for a request.
- **What to Provide**:
  - **File**: A PDF or image file (max 10MB).
- **Response**: Returns the updated request details.

### **3.2 Upload Receipt**
- **URL**: `/api/p2p/requests/<request_id>/upload_receipt/`
- **Method**: POST
- **Who**: Staff or finance users.
- **When**: To upload a receipt for a request.
- **What to Provide**:
  - **File**: A PDF or image file (max 10MB).
- **Response**: Returns the updated request details.

---

## 4. Purchase Order Endpoints

### **4.1 View All Purchase Orders**
- **URL**: `/api/p2p/orders/`
- **Method**: GET
- **Who**: Staff and finance users.
- **When**: To view all purchase orders.
- **What to Provide**: None.
- **Response**: Returns a list of purchase orders.

### **4.2 Update Order Status**
- **URL**: `/api/p2p/orders/<order_id>/update_status/`
- **Method**: POST
- **Who**: Finance users.
- **When**: To update the status of a purchase order.
- **What to Provide**:
  ```json
  {
    "status": "COMPLETED"
  }
  ```
- **Response**: Returns the updated order details.

---

## Notes
- Replace `<request_id>` and `<order_id>` with the actual IDs of the purchase request or order.
- Use the access token in the `Authorization` header for all authenticated requests:
  ```
  Authorization: Bearer <access_token>
  ```
- Ensure that the user roles and permissions are correctly set up to access the endpoints.

---

This guide should help you manually test and understand the workflow of the endpoints in the procure-to-pay system.