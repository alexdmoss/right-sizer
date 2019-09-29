from right_sizer import utils


def test_set_update_mode_is_on(monkeypatch):
    monkeypatch.setenv("UPDATE_MODE", "Auto")
    assert utils.set_update_mode() == "Auto"


def test_set_update_mode_is_random(monkeypatch):
    monkeypatch.setenv("UPDATE_MODE", "Floopy")
    assert utils.set_update_mode() == "Off"


def test_set_update_mode_is_not_set():
    assert utils.set_update_mode() == "Off"


def test_namespace_set(monkeypatch):
    monkeypatch.setenv("NAMESPACE", "floopy")
    assert utils.set_namespace() == "floopy"


def test_namespace_not_set():
    assert not utils.set_namespace()


def test_patching_enabled(monkeypatch):
    monkeypatch.setenv("PATCH_KUBE_SYSTEM", "True")
    assert utils.set_patch_kube_system()


def test_patching_set_but_off(monkeypatch):
    monkeypatch.setenv("PATCH_KUBE_SYSTEM", "Wowser")
    assert not utils.set_patch_kube_system()


def test_patching_set_to_off(monkeypatch):
    monkeypatch.setenv("PATCH_KUBE_SYSTEM", "False")
    assert not utils.set_patch_kube_system()


def test_patching_not_set():
    assert not utils.set_patch_kube_system()


def test_set_update_frequency(monkeypatch):
    monkeypatch.setenv("UPDATE_FREQUENCY", "1337")
    assert utils.set_update_frequency() == 1337


def test_set_update_frequency_default():
    assert utils.set_update_frequency() == 600
