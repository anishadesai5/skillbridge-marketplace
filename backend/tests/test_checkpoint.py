from datetime import date, timedelta


def create_test_booking(client,customer_headers):
    package_id=client.get("/services").json()[0]["package_id"]
    response=client.post("/bookings",headers=customer_headers,json={"package_id":package_id,"booking_date":str(date.today()+timedelta(days=3)),"customer_notes":"Checkpoint booking"})
    assert response.status_code==201
    return response.json()


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


def test_customer_can_create_booking_with_simulated_payment_hold(client,customer_headers):
    providers = client.get("/providers").json()
    package_id = providers[0]["packages"][0]["id"]
    response = client.post(
        "/bookings",
        json={
            "package_id": package_id,
            "booking_date": str(date.today() + timedelta(days=3)),
            "customer_notes": "Please focus on keyboard navigation.",
        },headers=customer_headers,
    )
    assert response.status_code == 201
    assert response.json()["payment_held"] is True
    assert response.json()["status"] == "Pending"
    assert response.json()["total"] == "450.00"
    assert response.json()["customer_notes"] == "Please focus on keyboard navigation."


def test_booking_rejects_past_date(client,customer_headers):
    providers = client.get("/providers").json()
    response = client.post(
        "/bookings",
        json={
            "package_id": providers[0]["packages"][0]["id"],
            "booking_date": str(date.today() - timedelta(days=1)),
        },headers=customer_headers,
    )
    assert response.status_code == 422
    assert "past" in response.json()["detail"]


def test_customer_registration_returns_token(client):
    response=client.post("/auth/register",json={"email":"new.customer@example.test","password":"Customer456!","role":"customer","first_name":"New","last_name":"Customer"})
    assert response.status_code==201
    assert response.json()["user"]["role"]=="customer"
    assert response.json()["access_token"]


def test_login_rejects_bad_password(client):
    response=client.post("/auth/login",json={"email":"customer@example.test","password":"wrong-password"})
    assert response.status_code==401


def test_provider_cannot_access_admin_route(client,provider_headers):
    response=client.get("/admin/providers/pending",headers=provider_headers)
    assert response.status_code==403


def test_admin_can_approve_pending_provider(client,admin_headers):
    registration=client.post("/auth/register",json={"email":"pending.provider@example.test","password":"Provider456!","role":"provider","first_name":"Pending","last_name":"Provider"})
    provider_token=registration.json()["access_token"]
    profile=client.get("/providers/me",headers={"Authorization":f"Bearer {provider_token}"}).json()
    client.post("/providers/me/credentials",headers={"Authorization":f"Bearer {provider_token}"},json={"credential_type":"Certificate","document_url":"https://example.test/certificate"})
    response=client.post(f"/admin/providers/{profile['id']}/decision",headers=admin_headers,json={"decision":"approve"})
    assert response.status_code==200
    assert response.json()["published"] is True
    assert response.json()["status"]=="Approved"


def test_service_search_supports_keyword_price_and_rating_filters(client):
    response=client.get("/services",params={"q":"accessibility","category":"Design","min_price":"400","max_price":"500","min_rating":"4.5"})
    assert response.status_code==200
    assert len(response.json())==1
    assert response.json()[0]["title"]=="UX Review"


def test_service_search_rejects_reversed_price_range(client):
    response=client.get("/services",params={"min_price":"500","max_price":"100"})
    assert response.status_code==422
    assert "Minimum price" in response.json()["detail"]


def test_unapproved_provider_is_excluded_from_search(client):
    from app.models import Provider, Role, ServicePackage, UserAccount
    from app.security import hash_password
    from conftest import TestingSession
    with TestingSession() as db:
        user=UserAccount(email="hidden@example.test",password_hash=hash_password("Provider123!"),role=Role.PROVIDER)
        db.add(user);db.flush()
        provider=Provider(user_id=user.id,first_name="Hidden",last_name="Provider",status="Pending",published=False,rating=5)
        db.add(provider);db.flush()
        db.add(ServicePackage(provider_id=provider.id,category="Design",title="Hidden service",description="Must not be public",price=10,duration_days=1))
        db.commit()
    response=client.get("/services",params={"q":"Hidden"})
    assert response.status_code==200
    assert response.json()==[]


def test_provider_detail_returns_only_public_active_packages(client):
    provider=client.get("/providers").json()[0]
    response=client.get(f"/providers/{provider['id']}")
    assert response.status_code==200
    assert response.json()["first_name"]=="Maya"
    assert all(package["title"]!="Inactive" for package in response.json()["packages"])


def test_missing_provider_detail_returns_404(client):
    assert client.get("/providers/99999").status_code==404


def test_customer_can_retrieve_persisted_booking(client,customer_headers):
    package_id=client.get("/services").json()[0]["package_id"]
    created=client.post("/bookings",headers=customer_headers,json={"package_id":package_id,"booking_date":str(date.today()+timedelta(days=2)),"customer_notes":"Morning preferred"})
    response=client.get("/customers/me/bookings",headers=customer_headers)
    assert response.status_code==200
    assert response.json()[0]["id"]==created.json()["id"]
    assert response.json()[0]["status"]=="Pending"


def test_provider_cannot_create_or_view_customer_bookings(client,provider_headers):
    package_id=client.get("/services").json()[0]["package_id"]
    payload={"package_id":package_id,"booking_date":str(date.today()+timedelta(days=2))}
    assert client.post("/bookings",headers=provider_headers,json=payload).status_code==403
    assert client.get("/customers/me/bookings",headers=provider_headers).status_code==403


def test_provider_can_confirm_pending_booking(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    response=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Confirmed"})
    assert response.status_code==200
    assert response.json()["status"]=="Confirmed"


def test_booking_rejects_skipped_status_transition(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    response=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Active"})
    assert response.status_code==422
    assert "Invalid transition" in response.json()["detail"]


def test_customer_can_cancel_but_cannot_confirm_booking(client,customer_headers):
    booking=create_test_booking(client,customer_headers)
    forbidden=client.patch(f"/bookings/{booking['id']}/status",headers=customer_headers,json={"status":"Confirmed"})
    assert forbidden.status_code==403
    cancelled=client.patch(f"/bookings/{booking['id']}/status",headers=customer_headers,json={"status":"Cancelled"})
    assert cancelled.status_code==200
    assert cancelled.json()["status"]=="Cancelled"


def test_provider_can_persist_milestones_totaling_100(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    response=client.put(f"/bookings/{booking['id']}/milestones",headers=provider_headers,json={"milestones":[
        {"sequence":1,"description":"Research and requirements","allocation_pct":"40.00"},
        {"sequence":2,"description":"Final delivery","allocation_pct":"60.00"},
    ]})
    assert response.status_code==200
    assert [item["sequence"] for item in response.json()]==[1,2]
    assert sum(float(item["allocation_pct"]) for item in response.json())==100
    detail=client.get(f"/bookings/{booking['id']}",headers=customer_headers)
    assert len(detail.json()["milestones"])==2


def test_milestone_batch_rejects_invalid_allocation_total(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    response=client.put(f"/bookings/{booking['id']}/milestones",headers=provider_headers,json={"milestones":[
        {"sequence":1,"description":"First delivery","allocation_pct":"40.00"},
        {"sequence":2,"description":"Second delivery","allocation_pct":"50.00"},
    ]})
    assert response.status_code==422
    detail=client.get(f"/bookings/{booking['id']}",headers=customer_headers)
    assert detail.json()["milestones"]==[]


def test_milestone_batch_rejects_duplicate_sequences(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    response=client.put(f"/bookings/{booking['id']}/milestones",headers=provider_headers,json={"milestones":[
        {"sequence":1,"description":"First delivery","allocation_pct":"50.00"},
        {"sequence":1,"description":"Second delivery","allocation_pct":"50.00"},
    ]})
    assert response.status_code==422
    assert "unique" in str(response.json()).lower()


def test_booking_requires_valid_milestones_before_work_starts(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Confirmed"})
    response=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Active"})
    assert response.status_code==422
    assert "needs milestones" in response.json()["detail"]


def test_booking_can_start_with_valid_milestones(client,customer_headers,provider_headers):
    booking=create_test_booking(client,customer_headers)
    milestones={"milestones":[{"sequence":1,"description":"Complete service","allocation_pct":"100.00"}]}
    assert client.put(f"/bookings/{booking['id']}/milestones",headers=provider_headers,json=milestones).status_code==200
    assert client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Confirmed"}).status_code==200
    response=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Active"})
    assert response.status_code==200
    assert response.json()["status"]=="Active"


def test_booking_requires_all_milestones_approved_before_completion(client,customer_headers,provider_headers):
    from app.models import Milestone, MilestoneStatus
    from conftest import TestingSession

    booking=create_test_booking(client,customer_headers)
    milestones={"milestones":[{"sequence":1,"description":"Complete service","allocation_pct":"100.00"}]}
    client.put(f"/bookings/{booking['id']}/milestones",headers=provider_headers,json=milestones)
    client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Confirmed"})
    client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Active"})

    blocked=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Completed"})
    assert blocked.status_code==422
    assert "approved" in blocked.json()["detail"].lower()

    with TestingSession() as db:
        milestone=db.query(Milestone).filter(Milestone.booking_id==booking["id"]).one()
        milestone.status=MilestoneStatus.APPROVED
        db.commit()

    completed=client.patch(f"/bookings/{booking['id']}/status",headers=provider_headers,json={"status":"Completed"})
    assert completed.status_code==200
    assert completed.json()["status"]=="Completed"
