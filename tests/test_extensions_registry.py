from noethys.Extensions import Extension, ExtensionRegistry


def test_register_and_lookup_extension():
    registry = ExtensionRegistry()
    extension = Extension(
        "communication.sms.demo",
        "Fournisseur SMS de démonstration",
        version="1.0",
        capabilities=("sms.send", "sms.status"),
    )

    registry.register(extension)

    assert registry.get("communication.sms.demo") is extension
    assert registry.all() == (extension,)
    assert registry.by_capability("sms.send") == (extension,)
    assert registry.by_capability("email.send") == ()


def test_duplicate_extension_is_rejected():
    registry = ExtensionRegistry()
    registry.register(Extension("demo", "Démo"))

    try:
        registry.register(Extension("demo", "Autre démo"))
    except ValueError as exc:
        assert "déjà enregistrée" in str(exc)
    else:
        raise AssertionError("Une extension dupliquée doit être refusée")


def test_factory_is_explicit_and_optional():
    registry = ExtensionRegistry()
    extension = registry.register(
        Extension("demo.factory", "Démo factory", factory=lambda value: {"value": value})
    )

    assert extension.create(42) == {"value": 42}
    assert Extension("demo.none", "Sans factory").create() is None


def test_unregister_and_clear():
    registry = ExtensionRegistry()
    registry.register(Extension("a", "A"))
    registry.register(Extension("b", "B"))

    assert registry.unregister("a").extension_id == "a"
    assert registry.get("a") is None

    registry.clear()
    assert registry.all() == ()
