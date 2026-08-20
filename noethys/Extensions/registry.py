# -*- coding: utf-8 -*-

"""Registre minimal d'extensions pour Noethys Desktop.

Ce module fournit un contrat simple et testable. Il ne réalise aucune
Découverte automatique dans le système de fichiers et n'importe aucun code
externe de manière implicite.
"""


class Extension(object):
    """Description d'une extension enregistrable dans Noethys."""

    def __init__(self, extension_id, name, version="", capabilities=None, factory=None):
        extension_id = (extension_id or "").strip()
        name = (name or "").strip()

        if not extension_id:
            raise ValueError("extension_id est obligatoire")
        if not name:
            raise ValueError("name est obligatoire")
        if factory is not None and not callable(factory):
            raise TypeError("factory doit être appelable ou None")

        self.extension_id = extension_id
        self.name = name
        self.version = (version or "").strip()
        self.capabilities = tuple(sorted(set(capabilities or ())))
        self.factory = factory

    def supports(self, capability):
        return capability in self.capabilities

    def create(self, *args, **kwargs):
        if self.factory is None:
            return None
        return self.factory(*args, **kwargs)


class ExtensionRegistry(object):
    """Registre explicite, déterministe et sans chargement dynamique implicite."""

    def __init__(self):
        self._extensions = {}

    def register(self, extension):
        if not isinstance(extension, Extension):
            raise TypeError("extension doit être une instance de Extension")
        if extension.extension_id in self._extensions:
            raise ValueError("Extension déjà enregistrée : %s" % extension.extension_id)
        self._extensions[extension.extension_id] = extension
        return extension

    def unregister(self, extension_id):
        return self._extensions.pop(extension_id, None)

    def get(self, extension_id, default=None):
        return self._extensions.get(extension_id, default)

    def all(self):
        return tuple(self._extensions[key] for key in sorted(self._extensions))

    def by_capability(self, capability):
        return tuple(
            extension
            for extension in self.all()
            if extension.supports(capability)
        )

    def clear(self):
        self._extensions.clear()


_REGISTRY = ExtensionRegistry()


def get_registry():
    """Retourne le registre global de l'application."""
    return _REGISTRY
