from datetime import date, timedelta


def test_health_confirms_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected", "payment_mode": "simulated"}


def test_customer_can_discover_published_provider(client):
    response = client.get("/providers", params={"category": "Design"})
    assert response.status_code == 200
    providers = response.json()
    assert providers[0]["first_name"] == "Maya"
    assert providers[0]["packages"][0]["title"] == "UX Review"


def test_customer_can_create_booking_with_simulated_payment_hold(client):
    providers = client.get("/providers").json()
    package_id = providers[0]["packages"][0]["id"]
    response = client.post(
        "/bookings",
        json={
            "customer_id": 1,
            "package_id": package_id,
            "booking_date": str(date.today() + timedelta(days=3)),
            "total": "450.00",
        },
    )
    assert response.status_code == 201
    assert response.json()["payment_held"] is True
    assert response.json()["status"] == "Pending"


def test_booking_rejects_price_mismatch(client):
    providers = client.get("/providers").json()
    response = client.post(
        "/bookings",
        json={
            "customer_id": 1,
            "package_id": providers[0]["packages"][0]["id"],
            "booking_date": str(date.today() + timedelta(days=3)),
            "total": "1.00",
        },
    )
    assert response.status_code == 422
    assert "equal the package price" in response.json()["detail"]
