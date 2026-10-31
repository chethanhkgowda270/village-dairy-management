def collect(client, farmer_id, **overrides):
    body = {
        "farmer_id": farmer_id, "date": "2026-10-01", "shift": "morning",
        "quantity_litres": 10, "fat": 4.0, "snf": 8.5,
    }
    body.update(overrides)
    return client.post("/collections", json=body)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_add_and_list_farmers(client, cow_farmer):
    assert cow_farmer["id"] == 1
    farmers = client.get("/farmers?village=Hosahalli").get_json()
    assert [f["name"] for f in farmers] == ["Ramesh"]
    assert client.get("/farmers?village=Other").get_json() == []


def test_farmer_validation(client):
    r = client.post("/farmers", json={"name": "A", "village": "V", "milk_type": "goat"})
    assert r.status_code == 400
    assert client.post("/farmers", json={"village": "V", "milk_type": "cow"}).status_code == 400


def test_collection_amount_is_calculated(client, cow_farmer):
    r = collect(client, cow_farmer["id"])
    assert r.status_code == 201
    body = r.get_json()
    assert body["rate_per_litre"] == 33.0
    assert body["amount"] == 330.0


def test_duplicate_shift_rejected(client, cow_farmer):
    collect(client, cow_farmer["id"])
    assert collect(client, cow_farmer["id"]).status_code == 409
    assert collect(client, cow_farmer["id"], shift="evening").status_code == 201


def test_collection_validation(client, cow_farmer):
    assert collect(client, cow_farmer["id"], fat=50).status_code == 400
    assert collect(client, cow_farmer["id"], quantity_litres=-1).status_code == 400
    assert collect(client, cow_farmer["id"], shift="noon").status_code == 400
    assert collect(client, 999).status_code == 404


def test_statement_and_balance(client, cow_farmer):
    fid = cow_farmer["id"]
    collect(client, fid)
    collect(client, fid, shift="evening", quantity_litres=5)
    client.post("/payments", json={"farmer_id": fid, "amount": 200, "date": "2026-10-05"})
    s = client.get(f"/farmers/{fid}/statement?from=2026-10-01&to=2026-10-10").get_json()
    assert s["total_litres"] == 15
    assert s["total_earned"] == 495.0
    assert s["total_paid"] == 200
    assert s["balance_due"] == 295.0


def test_daily_report(client, cow_farmer):
    collect(client, cow_farmer["id"])
    r = client.get("/reports/daily?date=2026-10-01").get_json()
    assert r["total_litres"] == 10
    assert r["total_amount"] == 330.0
    assert r["shifts"][0]["shift"] == "morning"


def test_home_page_serves_web_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Village Dairy" in r.data


def test_api_info(client):
    assert "try_these" in client.get("/api").get_json()


def test_rate_preview(client):
    r = client.get("/rate?milk_type=cow&fat=4&snf=8.5")
    assert r.get_json()["rate_per_litre"] == 33.0
    assert client.get("/rate?milk_type=goat&fat=4&snf=8").status_code == 400
    assert client.get("/rate?milk_type=cow&fat=abc&snf=8").status_code == 400


def test_trailing_slash_and_favicon_do_not_404(client):
    assert client.get("/farmers/").status_code == 200
    assert client.get("/favicon.ico").status_code == 204


def test_unknown_url_returns_404(client):
    assert client.get("/nothing-here").status_code == 404
