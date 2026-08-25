from app.services.leads import find_existing_lead, upsert_lead


def test_dedup_by_source_id(db_session, make_lead):
    lead = make_lead(source="google_places", source_id="abc123")
    normalized = {"source": "google_places", "source_id": "abc123"}
    found = find_existing_lead(db_session, normalized)
    assert found.id == lead.id


def test_dedup_by_normalized_website(db_session, make_lead):
    lead = make_lead(normalized_website="samecafe.com", source_id="unique-1")
    normalized = {
        "source": "google_places",
        "source_id": "different-id",
        "normalized_website": "samecafe.com",
    }
    found = find_existing_lead(db_session, normalized)
    assert found.id == lead.id


def test_dedup_by_normalized_phone(db_session, make_lead):
    lead = make_lead(normalized_phone="03001234567", source_id="unique-2")
    normalized = {
        "source": "google_places",
        "source_id": "different-id-2",
        "normalized_phone": "03001234567",
    }
    found = find_existing_lead(db_session, normalized)
    assert found.id == lead.id


def test_dedup_by_name_and_address(db_session, make_lead):
    lead = make_lead(
        business_name="Unique Cafe Name",
        address="789 Rare Street",
        source_id="unique-3",
    )
    normalized = {
        "source": "google_places",
        "source_id": "different-id-3",
        "business_name": "Unique Cafe Name",
        "address": "789 Rare Street",
    }
    found = find_existing_lead(db_session, normalized)
    assert found.id == lead.id


def test_no_duplicate_found_for_genuinely_new_lead(db_session, make_lead):
    make_lead(source_id="existing")
    normalized = {
        "source": "google_places",
        "source_id": "brand-new",
        "normalized_website": "totallydifferent.com",
        "normalized_phone": "0000000000",
        "business_name": "Totally Different Business",
        "address": "Nowhere",
    }
    assert find_existing_lead(db_session, normalized) is None


def test_upsert_creates_new_lead_and_raw_record(db_session):
    normalized = {
        "business_name": "New Business",
        "category": "Hotel",
        "address": None,
        "city": None,
        "country": None,
        "latitude": None,
        "longitude": None,
        "phone": None,
        "normalized_phone": None,
        "email": None,
        "website": None,
        "normalized_website": None,
        "social_links": None,
        "source": "google_places",
        "source_id": "brand-new-2",
        "source_url": None,
        "rating": None,
        "review_count": None,
    }
    lead, is_new = upsert_lead(db_session, normalized, raw_place={"id": "brand-new-2"})
    db_session.commit()
    assert is_new is True
    assert lead.business_name == "New Business"
    assert len(lead.raw_records) == 1


def test_upsert_updates_last_seen_on_duplicate(db_session, make_lead):
    lead = make_lead(source_id="dup-test")
    original_last_seen = lead.last_seen

    normalized = {
        "business_name": lead.business_name,
        "source": "google_places",
        "source_id": "dup-test",
    }
    found_lead, is_new = upsert_lead(db_session, normalized, raw_place={"id": "dup-test"})
    db_session.commit()

    assert is_new is False
    assert found_lead.id == lead.id
    assert found_lead.last_seen >= original_last_seen
    assert len(found_lead.raw_records) == 1
