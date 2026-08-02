# -*- coding: utf-8 -*-
"""Compatibilité Noethys avec le moteur vocal moderne pyttsx3.

Le code historique importe ``pyttsx``. Ce module conserve cette API minimale
sans imposer une modification diffuse des modules applicatifs.
"""
from pyttsx3 import *  # noqa: F401,F403
from pyttsx3 import init

__all__ = ["init"]
