"""
Tests for blood request API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestBloodRequestEndpoints:
    """Test blood request management endpoints."""

    @pytest.mark.asyncio
    async def test_get_pending_requests_empty(self, client: AsyncClient):
        """Test getting pending requests when empty."""
        response = await client.get("/api/v1/blood-requests/pending")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_ongoing_requests_empty(self, client: AsyncClient):
        """Test getting ongoing requests when empty."""
        response = await client.get("/api/v1/blood-requests/ongoing")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_closed_requests_empty(self, client: AsyncClient):
        """Test getting closed requests when empty."""
        response = await client.get("/api/v1/blood-requests/closed")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_request_stats(self, client: AsyncClient):
        """Test getting blood request statistics."""
        response = await client.get("/api/v1/blood-requests/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "by_status" in data
        assert "by_blood_group" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_blood_request_not_found(self, client: AsyncClient):
        """Test getting non-existent blood request returns 404."""
        response = await client.get("/api/v1/blood-requests/REQ-nonexistent")
        
        assert response.status_code == 404


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client: AsyncClient):
        """Test dashboard statistics endpoint."""
        response = await client.get("/api/v1/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert "donors" in data
        assert "hospitals" in data

    @pytest.mark.asyncio
    async def test_donors_by_blood_group(self, client: AsyncClient):
        """Test donors by blood group analytics."""
        response = await client.get("/api/v1/analytics/donors/by-blood-group")
        
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    @pytest.mark.asyncio
    async def test_donors_by_city(self, client: AsyncClient):
        """Test donors by city analytics."""
        response = await client.get("/api/v1/analytics/donors/by-city")
        
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    @pytest.mark.asyncio
    async def test_monthly_request_stats(self, client: AsyncClient):
        """Test monthly request statistics."""
        response = await client.get("/api/v1/analytics/requests/monthly")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
