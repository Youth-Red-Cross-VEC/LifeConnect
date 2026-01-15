"""
Tests for hospital API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestHospitalEndpoints:
    """Test hospital management endpoints."""

    @pytest.mark.asyncio
    async def test_list_hospitals_empty(self, client: AsyncClient):
        """Test listing hospitals when database is empty."""
        response = await client.get("/api/v1/hospitals/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_hospital(self, client: AsyncClient):
        """Test creating a new hospital."""
        hospital_data = {
            "hospital_name": "Test Hospital",
            "hospital_address": "123 Healthcare Road",
            "pincode": "600001",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India",
            "branch": "Main",
            "landmark": "Near Test Station"
        }
        
        response = await client.post("/api/v1/hospitals/", json=hospital_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["hospital_name"] == "Test Hospital"
        assert data["city"] == "Chennai"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_hospital(self, client: AsyncClient):
        """Test getting a hospital by ID."""
        # First create a hospital
        hospital_data = {
            "hospital_name": "Apollo Hospital",
            "hospital_address": "456 Medical Avenue",
            "pincode": "600002",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India"
        }
        
        create_response = await client.post("/api/v1/hospitals/", json=hospital_data)
        hospital_id = create_response.json()["id"]
        
        # Then get it
        response = await client.get(f"/api/v1/hospitals/{hospital_id}")
        
        assert response.status_code == 200
        assert response.json()["hospital_name"] == "Apollo Hospital"

    @pytest.mark.asyncio
    async def test_hospital_autofill(self, client: AsyncClient):
        """Test hospital autofill suggestions."""
        # Create a hospital first
        hospital_data = {
            "hospital_name": "Government General Hospital",
            "hospital_address": "789 Public Road",
            "pincode": "600003",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India"
        }
        await client.post("/api/v1/hospitals/", json=hospital_data)
        
        # Test autofill
        response = await client.get("/api/v1/hospitals/autofill?q=Government")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_cities(self, client: AsyncClient):
        """Test getting list of cities with hospitals."""
        response = await client.get("/api/v1/hospitals/cities")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio  
    async def test_get_hospital_not_found(self, client: AsyncClient):
        """Test getting non-existent hospital returns 404."""
        response = await client.get("/api/v1/hospitals/HSP-nonexistent")
        
        assert response.status_code == 404
