from app.schemas.common import AttestationDirection


def test_registries_are_loaded_into_app_state_on_startup(client):
    app = client.app

    template_entry = app.state.template_registry.get("demo", AttestationDirection.EQUIPMENT)
    assert template_entry is not None

    ac_entry = app.state.ac_registry.get("demo")
    assert ac_entry is not None
    assert ac_entry.name == "Демо-АЦ"
