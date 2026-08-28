from app.services import events


def test_events_service_module_exports_list_events():
    assert callable(events.list_events)
