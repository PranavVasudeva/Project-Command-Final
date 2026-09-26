def test_incident_windows_and_category_filters_return_expected_feed(client):
    all_feed = client.get("/incidents", params={"range": "all"})
    assert all_feed.status_code == 200, all_feed.text
    all_data = all_feed.json()
    # total_incidents is the sum of each zone's representative incident count -
    # assert against that computed total instead of a hardcoded snapshot value.
    assert all_data["total_incidents"] == sum(zone["incidents"] for zone in all_data["zones"])
    assert all_data["high_risk_zone_id"] == "zone-1"
    assert any(zone["name"] == "KIIT Square Junction" and zone["risk_level"] == "CRITICAL" for zone in all_data["zones"])
    assert all_data["filtered_incidents"] == len(all_data["incidents"])

    week = client.get("/incidents", params={"range": "7d"})
    assert week.status_code == 200
    assert week.json()["filtered_incidents"] < all_data["filtered_incidents"]

    category = client.get("/incidents", params={"range": "all", "category": "Traffic Accident"})
    assert category.status_code == 200
    assert category.json()["filtered_incidents"] > 0
    assert all(item["category"] == "Traffic Accident" for item in category.json()["incidents"])
