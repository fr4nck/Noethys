#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Panneau d'accueil « Aujourd'hui / Échéancier ».

Le contrôle conserve le point d'accroche historique ``CTRL_Ephemeride.CTRL``
mais sa présentation suit le cockpit Repens Design. La météo ne dépend plus de
coordonnées GPS déjà saisies : ville/code postal peuvent être géocodés et mis en
cache localement sans modifier la base métier.
"""

import datetime
import json
import threading

import wx
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen

import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Config
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils import UTILS_VacancesScolaires

try:
    from Utils.UTILS_Astral import City
except Exception:
    City = None


JOURS = (
    _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
    _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
)
MOIS = (
    _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"),
    _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"),
    _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"),
)

LIBELLES_METEO = {
    0: _(u"ciel dégagé"), 1: _(u"plutôt dégagé"),
    2: _(u"partiellement nuageux"), 3: _(u"couvert"),
    45: _(u"brouillard"), 48: _(u"brouillard givrant"),
    51: _(u"bruine faible"), 53: _(u"bruine"), 55: _(u"bruine forte"),
    61: _(u"pluie faible"), 63: _(u"pluie"), 65: _(u"forte pluie"),
    71: _(u"neige faible"), 73: _(u"neige"), 75: _(u"fortes chutes de neige"),
    80: _(u"averses faibles"), 81: _(u"averses"), 82: _(u"fortes averses"),
    95: _(u"orage"), 96: _(u"orage avec grêle"), 99: _(u"fort orage avec grêle"),
}

PARAM_CACHE_GEOCODAGE = "dashboard_geocodage_cache"


def DateDDEnDateFR(date_dd):
    return u"%s %d %s %d" % (
        JOURS[date_dd.weekday()], date_dd.day, MOIS[date_dd.month - 1], date_dd.year
    )


def _heure_iso(valeur):
    if not valeur:
        return None
    try:
        return valeur.split("T", 1)[1][:5]
    except Exception:
        return None


class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.dateJour = datetime.date.today()
        self.dictOrganisateur = None
        self._chargement_en_cours = False

        # Deux surfaces fonctionnelles remplacent l'ancienne ligne de texte
        # séparée par un trait vertical. Elles restent compactes et desktop.
        self.panel_jour = wx.Panel(self, style=wx.TAB_TRAVERSAL)
        self.panel_echeances = wx.Panel(self, style=wx.TAB_TRAVERSAL)

        self.ctrl_sur_titre = wx.StaticText(self.panel_jour, -1, _(u"AUJOURD'HUI"))
        self.ctrl_date = wx.StaticText(self.panel_jour, -1, DateDDEnDateFR(self.dateJour))
        self.ctrl_lieu = wx.StaticText(self.panel_jour, -1, _(u"Localisation de l'organisateur"))
        self.ctrl_meteo = wx.StaticText(self.panel_jour, -1, _(u"Météo : chargement…"))
        self.ctrl_soleil = wx.StaticText(self.panel_jour, -1, _(u"Soleil : chargement…"))

        self.ctrl_sur_titre_echeances = wx.StaticText(self.panel_echeances, -1, _(u"ÉCHÉANCIER"))
        self.ctrl_titre_echeances = wx.StaticText(self.panel_echeances, -1, _(u"À venir"))
        self.ctrl_echeances = wx.StaticText(self.panel_echeances, -1, _(u"Chargement de l'échéancier…"))

        self._AppliqueApparence()
        self._ConstruitLayout()

    def _Police(self, poids=wx.FONTWEIGHT_NORMAL, delta=0):
        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        taille = max(7, police.GetPointSize() + delta)
        police.SetPointSize(taille)
        police.SetWeight(poids)
        return police

    def _AppliqueApparence(self):
        fond = UTILS_Interface.GetCouleurRole("surface")
        fond_jour = UTILS_Interface.GetCouleurRole("surface_container_low")
        fond_echeances = UTILS_Interface.GetCouleurRole("surface_container")
        texte = UTILS_Interface.GetCouleurRole("on_surface")
        secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant")
        accent = UTILS_Interface.GetCouleurRole("primary")

        self.SetBackgroundColour(fond)
        self.panel_jour.SetBackgroundColour(fond_jour)
        self.panel_echeances.SetBackgroundColour(fond_echeances)

        for ctrl, fond_ctrl in (
            (self.ctrl_sur_titre, fond_jour),
            (self.ctrl_date, fond_jour),
            (self.ctrl_lieu, fond_jour),
            (self.ctrl_meteo, fond_jour),
            (self.ctrl_soleil, fond_jour),
            (self.ctrl_sur_titre_echeances, fond_echeances),
            (self.ctrl_titre_echeances, fond_echeances),
            (self.ctrl_echeances, fond_echeances),
        ):
            ctrl.SetBackgroundColour(fond_ctrl)

        for ctrl in (self.ctrl_sur_titre, self.ctrl_sur_titre_echeances):
            ctrl.SetForegroundColour(accent)
            ctrl.SetFont(self._Police(wx.FONTWEIGHT_BOLD, -1))

        self.ctrl_date.SetForegroundColour(texte)
        self.ctrl_date.SetFont(self._Police(wx.FONTWEIGHT_BOLD, 2))
        self.ctrl_titre_echeances.SetForegroundColour(texte)
        self.ctrl_titre_echeances.SetFont(self._Police(wx.FONTWEIGHT_BOLD, 2))

        for ctrl in (self.ctrl_lieu, self.ctrl_meteo, self.ctrl_soleil, self.ctrl_echeances):
            ctrl.SetForegroundColour(secondaire)
            ctrl.SetFont(self._Police())

    def _ConstruitLayout(self):
        marge = UTILS_UIMetrics.spacing(2)
        espace = UTILS_UIMetrics.spacing(1)

        sizer_jour = wx.BoxSizer(wx.VERTICAL)
        sizer_jour.Add(self.ctrl_sur_titre, 0, wx.BOTTOM, espace)
        sizer_jour.Add(self.ctrl_date, 0, wx.BOTTOM, espace)
        sizer_jour.Add(self.ctrl_lieu, 0, wx.BOTTOM, UTILS_UIMetrics.px(2))
        sizer_jour.Add(self.ctrl_meteo, 0, wx.BOTTOM, UTILS_UIMetrics.px(2))
        sizer_jour.Add(self.ctrl_soleil, 0)
        self.panel_jour.SetSizer(sizer_jour)

        sizer_echeances = wx.BoxSizer(wx.VERTICAL)
        sizer_echeances.Add(self.ctrl_sur_titre_echeances, 0, wx.BOTTOM, espace)
        sizer_echeances.Add(self.ctrl_titre_echeances, 0, wx.BOTTOM, espace)
        sizer_echeances.Add(self.ctrl_echeances, 1, wx.EXPAND)
        self.panel_echeances.SetSizer(sizer_echeances)

        # La partie échéancier absorbe davantage de largeur : elle porte le
        # contenu variable. La partie journée conserve seulement sa taille utile.
        sizer_principal = wx.BoxSizer(wx.HORIZONTAL)
        sizer_principal.Add(self.panel_jour, 2, wx.EXPAND | wx.ALL, marge)
        sizer_principal.Add(
            self.panel_echeances,
            3,
            wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM,
            marge,
        )
        self.SetSizer(sizer_principal)
        self.Layout()

    def _ActualisePaneAui(self):
        parent = self.GetParent()
        gestionnaire = getattr(parent, "_mgr", None)
        if gestionnaire is None:
            return
        try:
            pane = gestionnaire.GetPane(self)
            if not pane.IsOk():
                return
            hauteur_min = UTILS_UIMetrics.panel_min_height("secondary")
            hauteur_ideale = max(hauteur_min, UTILS_UIMetrics.px(118))
            pane.Caption(_(u"Aujourd'hui / Échéancier"))
            pane.MinSize((-1, hauteur_min))
            pane.BestSize((-1, hauteur_ideale))
            gestionnaire.Update()
        except Exception:
            pass

    def Initialisation(self):
        self._ActualisePaneAui()
        if self._chargement_en_cours:
            return
        self._chargement_en_cours = True
        thread = threading.Thread(target=self._ChargeInformations, name="Noethys-AujourdHui")
        thread.daemon = True
        thread.start()

    def StartTicker(self):
        self.Initialisation()

    def StopTicker(self):
        pass

    def _ChargeInformations(self):
        try:
            organisateur = self._GetOrganisateur()
            self.dictOrganisateur = organisateur

            ville = organisateur.get("ville", "") if organisateur else ""
            if ville:
                wx.CallAfter(self.ctrl_lieu.SetLabel, ville)

            self._ResoudreCoordonnees(organisateur)

            meteo = None
            try:
                meteo = self._GetMeteoOpenMeteo(organisateur)
            except Exception:
                meteo = None

            if meteo:
                wx.CallAfter(self._AfficheMeteo, meteo)
            else:
                if organisateur.get("lat") is None or organisateur.get("long") is None:
                    message_meteo = _(u"Météo : localisation indisponible")
                else:
                    message_meteo = _(u"Météo : données indisponibles")
                wx.CallAfter(self.ctrl_meteo.SetLabel, message_meteo)
                soleil = self._GetSoleilLocal(organisateur)
                wx.CallAfter(
                    self.ctrl_soleil.SetLabel,
                    soleil or _(u"Soleil : horaires indisponibles"),
                )

            wx.CallAfter(self._ChargeEcheances)
        except Exception:
            try:
                wx.CallAfter(self.ctrl_meteo.SetLabel, _(u"Météo : données indisponibles"))
                wx.CallAfter(self.ctrl_soleil.SetLabel, _(u"Soleil : horaires indisponibles"))
                wx.CallAfter(self._ChargeEcheances)
            except Exception:
                pass
        finally:
            self._chargement_en_cours = False

    def _GetOrganisateur(self):
        db = GestionDB.DB()
        try:
            db.ExecuterReq("SELECT cp, ville, gps FROM organisateur WHERE IDorganisateur=1;")
            resultat = db.ResultatReq()
            if not resultat:
                return {}
            cp, ville, gps = resultat[0]
            cp, ville = cp or "", ville or ""
            lat = long = None
            if gps:
                try:
                    lat, long = gps.split(";", 1)
                    lat, long = float(lat), float(long)
                except Exception:
                    lat = long = None
            return {"cp": cp, "ville": ville, "lat": lat, "long": long}
        finally:
            db.Close()

    def _CleGeocodage(self, organisateur):
        cp = (organisateur.get("cp") or "").strip()
        ville = (organisateur.get("ville") or "").strip().lower()
        return u"%s|%s" % (cp, ville)

    def _ResoudreCoordonnees(self, organisateur):
        if not organisateur:
            return False
        if organisateur.get("lat") is not None and organisateur.get("long") is not None:
            return True

        cle = self._CleGeocodage(organisateur)
        cache = UTILS_Config.GetParametre(PARAM_CACHE_GEOCODAGE, {})
        if not isinstance(cache, dict):
            cache = {}
        valeur = cache.get(cle)
        if isinstance(valeur, (list, tuple)) and len(valeur) == 2:
            try:
                organisateur["lat"] = float(valeur[0])
                organisateur["long"] = float(valeur[1])
                return True
            except Exception:
                pass

        coordonnees = self._GeocoderOpenMeteo(organisateur)
        if coordonnees is None:
            return False

        lat, long = coordonnees
        organisateur["lat"], organisateur["long"] = lat, long
        cache[cle] = [lat, long]
        try:
            UTILS_Config.SetParametre(PARAM_CACHE_GEOCODAGE, cache)
        except Exception:
            pass
        return True

    def _GeocoderOpenMeteo(self, organisateur):
        ville = (organisateur.get("ville") or "").strip()
        if not ville:
            return None

        params = urlencode({
            "name": ville,
            "count": 8,
            "language": "fr",
            "format": "json",
        })
        reponse = urlopen("https://geocoding-api.open-meteo.com/v1/search?%s" % params, timeout=4)
        try:
            donnees = json.loads(reponse.read().decode("utf-8"))
        finally:
            try:
                reponse.close()
            except Exception:
                pass

        resultats = donnees.get("results") or []
        if not resultats:
            return None

        resultat = resultats[0]
        for candidat in resultats:
            if candidat.get("country_code") == "FR":
                resultat = candidat
                break

        try:
            return float(resultat["latitude"]), float(resultat["longitude"])
        except Exception:
            return None

    def _GetMeteoOpenMeteo(self, organisateur):
        if not organisateur:
            return None
        lat, long = organisateur.get("lat"), organisateur.get("long")
        if lat is None or long is None:
            return None

        params = urlencode({
            "latitude": lat,
            "longitude": long,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "sunrise,sunset",
            "forecast_days": 2,
            "timezone": "auto",
        })
        reponse = urlopen("https://api.open-meteo.com/v1/forecast?%s" % params, timeout=4)
        try:
            donnees = json.loads(reponse.read().decode("utf-8"))
        finally:
            try:
                reponse.close()
            except Exception:
                pass

        actuel = donnees.get("current", {})
        quotidien = donnees.get("daily", {})
        levers = quotidien.get("sunrise", [])
        couchers = quotidien.get("sunset", [])
        return {
            "temperature": actuel.get("temperature_2m"),
            "code": actuel.get("weather_code"),
            "vent": actuel.get("wind_speed_10m"),
            "lever": _heure_iso(levers[0]) if levers else None,
            "coucher": _heure_iso(couchers[0]) if couchers else None,
        }

    def _AfficheMeteo(self, meteo):
        condition = LIBELLES_METEO.get(meteo.get("code"), _(u"conditions variables"))
        morceaux = [_(u"Météo : %s") % condition]
        if meteo.get("temperature") is not None:
            morceaux.append(u"%s °C" % meteo["temperature"])
        if meteo.get("vent") is not None:
            morceaux.append(_(u"vent %s km/h") % meteo["vent"])
        self.ctrl_meteo.SetLabel(u" · ".join(morceaux))

        lever, coucher = meteo.get("lever"), meteo.get("coucher")
        if lever and coucher:
            self.ctrl_soleil.SetLabel(_(u"Soleil : lever %s · coucher %s") % (lever, coucher))
        else:
            self.ctrl_soleil.SetLabel(
                self._GetSoleilLocal(self.dictOrganisateur) or _(u"Soleil : horaires indisponibles")
            )
        self.Layout()

    def _GetSoleilLocal(self, organisateur):
        if City is None or not organisateur:
            return None
        ville = organisateur.get("ville")
        lat, long = organisateur.get("lat"), organisateur.get("long")
        if not ville or lat is None or long is None:
            return None
        try:
            city = City((ville, "France", float(lat), float(long), "Europe/Paris"))
            lever, coucher = city.sunrise(), city.sunset()
            return _(u"Soleil : lever %02d:%02d · coucher %02d:%02d") % (
                lever.hour, lever.minute, coucher.hour, coucher.minute
            )
        except Exception:
            return None

    def _ChargeEcheances(self):
        aujourd_hui = datetime.date.today()
        echeances = []

        donnees = UTILS_Config.GetParametre("dashboard_echeances", [])
        if isinstance(donnees, (list, tuple)):
            for item in donnees:
                if not isinstance(item, dict):
                    continue
                label = item.get("label") or item.get("titre")
                date_texte = item.get("date")
                if not label or not date_texte:
                    continue
                try:
                    date_dd = datetime.datetime.strptime(date_texte[:10], "%Y-%m-%d").date()
                except Exception:
                    continue
                if date_dd >= aujourd_hui:
                    echeances.append((date_dd, label))

        cp = self.dictOrganisateur.get("cp") if self.dictOrganisateur else None
        zone = UTILS_VacancesScolaires.GetZoneDepuisCodePostal(cp)
        periode = UTILS_VacancesScolaires.GetProchainePeriode(zone, aujourd_hui) if zone else None
        if periode is not None:
            debut = periode["debut"]
            reprise = periode["reprise"]
            if reprise is None:
                label = _(u"Vacances zone %s : %s · fin des cours %s") % (
                    zone, periode["nom"], debut.strftime("%d/%m")
                )
            else:
                label = _(u"Vacances zone %s : %s · départ %s · reprise %s") % (
                    zone, periode["nom"], debut.strftime("%d/%m"), reprise.strftime("%d/%m")
                )
            cle_tri = max(aujourd_hui, debut)
            echeances.append((cle_tri, label))

        echeances.sort(key=lambda valeur: valeur[0])
        echeances = echeances[:4]
        if not echeances:
            self.ctrl_echeances.SetLabel(
                _(u"Aucune échéance à venir · ajoutez les échéances métier dans la configuration du dashboard.")
            )
            return

        lignes = []
        for date_dd, label in echeances:
            delta = (date_dd - aujourd_hui).days
            if delta == 0:
                prefixe = _(u"Aujourd'hui")
            elif delta == 1:
                prefixe = _(u"Demain")
            else:
                prefixe = date_dd.strftime("%d/%m")
            lignes.append(u"%s — %s" % (prefixe, label))
        self.ctrl_echeances.SetLabel(u"\n".join(lignes))
        self.Layout()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.ctrl = CTRL(panel)
        sizer.Add(self.ctrl, 1, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(sizer)
        self.SetSize((1000, 220))
        self.CentreOnScreen()
        self.ctrl.Initialisation()


if __name__ == '__main__':
    app = wx.App(0)
    frame = MyFrame(None, -1, u"Aujourd'hui")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
