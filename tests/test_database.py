import database


def test_monday_has_no_workshop(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    assert database.get_workshops_for_day(db_path, 0) == []


def test_tuesday_has_two_workshops(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    workshops = database.get_workshops_for_day(db_path, 1)
    assert len(workshops) == 2
    names = {w["name"] for w in workshops}
    assert names == {"Honors Geometry", "MS Spanish 2"}


def test_wednesday_has_one_workshop(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    workshops = database.get_workshops_for_day(db_path, 2)
    assert len(workshops) == 1
    assert workshops[0]["name"] == "8th Grade Science"


def test_thursday_has_one_workshop(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    workshops = database.get_workshops_for_day(db_path, 3)
    assert len(workshops) == 1
    assert workshops[0]["name"] == "Adv 8th Grade English"


def test_friday_has_one_workshop(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    workshops = database.get_workshops_for_day(db_path, 4)
    assert len(workshops) == 1
    assert workshops[0]["name"] == "Adv US History"


def test_zoom_urls_preserved_exactly(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    tuesday = {w["name"]: w["zoom_url"] for w in database.get_workshops_for_day(db_path, 1)}
    assert tuesday["Honors Geometry"] == "https://springeducationgroup.zoom.us/j/91759775467"
    assert tuesday["MS Spanish 2"] == (
        "https://springeducationgroup.zoom.us/j/5705096276?pwd=E7sXftivTwju2VaaFn9P7qLbBRPD70.1"
    )


def test_init_db_is_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    database.init_db(db_path)
    database.init_db(db_path)

    total = sum(len(v) for v in database.get_full_week_schedule(db_path).values())
    assert total == 5  # 2 (Tue) + 1 (Wed) + 1 (Thu) + 1 (Fri)


def test_restart_does_not_duplicate_entries(tmp_path):
    """Simulates the bot process restarting: init_db is called again on a
    database that already has the schedule persisted from a prior run."""
    db_path = str(tmp_path / "test.db")

    database.init_db(db_path)  # first "boot"
    first_count = sum(len(v) for v in database.get_full_week_schedule(db_path).values())

    database.init_db(db_path)  # simulated restart
    second_count = sum(len(v) for v in database.get_full_week_schedule(db_path).values())

    assert first_count == second_count == 5
    tuesday = database.get_workshops_for_day(db_path, 1)
    assert len(tuesday) == 2  # not duplicated to 4


def test_full_week_schedule_covers_monday_through_friday(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    week = database.get_full_week_schedule(db_path)
    assert set(week.keys()) == {0, 1, 2, 3, 4}
    assert week[0] == []
