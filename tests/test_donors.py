"""
Tests for donor API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestDonorEndpoints:
    """Test donor management endpoints."""

    @pytest.mark.asyncio
    async def test_list_donors_empty(self, admin_client: AsyncClient):
        """Test listing donors when database is empty (admin required)."""
        response = await admin_client.get("/api/v1/donors/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_get_donor_not_found(self, client: AsyncClient):
        """Test getting a non-existent donor returns 404."""
        response = await client.get("/api/v1/donors/DON-nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_donor(self, client: AsyncClient):
        """Test registering a new donor."""
        donor_data = {
            "name": "Test Donor",
            "email": "testdonor@example.com",
            "password": "SecurePass123",
            "blood_group": "O+",
            "personal_details": {
                "first_name": "Test",
                "last_name": "Donor",
                "age": 25,
                "date_of_birth": "1999-01-15",
                "contact_number": "+919876543210"
            },
            "address_details": {
                "address": "123 Test Street",
                "pincode": "600001",
                "country": "India",
                "state": "Tamil Nadu",
                "city": "Chennai"
            },
            "disease_details": {
                "name": "None",
                "description": "No known diseases"
            }
        }
        
        response = await client.post("/api/v1/donors/register", json=donor_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Donor"
        assert data["email"] == "testdonor@example.com"
        assert data["blood_group"] == "O+"
        assert data["active_status"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_donor_duplicate_email(self, client: AsyncClient):
        """Test that registering with duplicate email fails."""
        donor_data = {
            "name": "First Donor",
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "blood_group": "A+",
            "personal_details": {
                "first_name": "First",
                "last_name": "Donor",
                "age": 25,
                "date_of_birth": "1999-01-15",
                "contact_number": "+919876543210"
            },
            "address_details": {
                "address": "123 Test Street",
                "pincode": "600001",
                "country": "India",
                "state": "Tamil Nadu",
                "city": "Chennai"
            },
            "disease_details": {
                "name": "None"
            }
        }
        
        # First registration should succeed
        response1 = await client.post("/api/v1/donors/register", json=donor_data)
        assert response1.status_code == 201
        
        # Second registration with same email should fail
        donor_data["name"] = "Second Donor"
        response2 = await client.post("/api/v1/donors/register", json=donor_data)
        assert response2.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_register_donor_invalid_blood_group(self, client: AsyncClient):
        """Test that invalid blood group is rejected."""
        donor_data = {
            "name": "Invalid Donor",
            "email": "invalid@example.com",
            "password": "SecurePass789",
            "blood_group": "X+",  # Invalid
            "personal_details": {
                "first_name": "Invalid",
                "last_name": "Donor",
                "age": 25,
                "date_of_birth": "1999-01-01",
                "contact_number": "+919876543212"
            },
            "address_details": {
                "address": "Test",
                "pincode": "600001",
                "country": "India",
                "state": "Tamil Nadu",
                "city": "Chennai"
            },
            "disease_details": {
                "name": "None"
            }
        }
        
        response = await client.post("/api/v1/donors/register", json=donor_data)
        
        assert response.status_code == 422  # Validation error
