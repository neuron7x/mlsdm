def test_defusedxml_resolvable():
    import importlib

    assert importlib.import_module("defusedxml.ElementTree")
