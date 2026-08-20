#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
if 'phoenix' in wx.PlatformInfo:
    from wx.adv import OwnerDrawnComboBox, ODCB_PAINTING_CONTROL, ODCB_PAINTING_SELECTED
else :
    from wx.combo import OwnerDrawnComboBox, ODCB_PAINTING_CONTROL, ODCB_PAINTING_SELECTED
import wx.lib.wordwrap as wordwrap


class CTRL(OwnerDrawnComboBox):
    def __init__(self, parent, donnees=[], nbreLignesDescription=1, wrap=False, hauteur=None, style=wx.CB_READONLY) :
        self.donnees = donnees
        self.nbreLignesDescription = nbreLignesDescription
        facteur_interface = UTILS_Interface.GetEchelle() / 100.0
        facteur_texte = facteur_interface * (UTILS_Interface.GetTailleTexte() / 100.0)
        # Le contrôle reste dense, mais sa hauteur minimale suit la taille du
        # texte afin d'éviter tout rognage avec les réglages d'accessibilité.
        facteur_hauteur = max(facteur_interface, facteur_texte)
        if hauteur == None :
            self.hauteurItem = max(28, int(round((33 + (self.nbreLignesDescription * 14)) * facteur_hauteur)))
        else :
            self.hauteurItem = max(20, int(round(hauteur * facteur_interface)))
        self.wrap = wrap
        self.selection = None
            
        # Init du contrôle
        listeLabels = []
        for donnee in self.donnees :
            listeLabels.append(donnee["label"])

        OwnerDrawnComboBox.__init__(self, parent, -1, choices=listeLabels, size=(-1, self.hauteurItem), style=style)
        try:
            UTILS_Interface.AppliquerAffichage(self, recursif=False)
        except Exception:
            pass

        self.Bind(wx.EVT_COMBOBOX, self.OnSelection)

    def _Police(self, coefficient=1.0, gras=False):
        """Retourne une police dérivée de la police réellement héritée."""
        try:
            police = wx.Font(self.GetFont())
            if not police.IsOk():
                police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            if hasattr(police, "GetFractionalPointSize") and hasattr(police, "SetFractionalPointSize"):
                taille = max(5.0, police.GetFractionalPointSize() * coefficient)
                police.SetFractionalPointSize(taille)
            else :
                police.SetPointSize(max(5, int(round(police.GetPointSize() * coefficient))))
            if gras:
                police.SetWeight(wx.FONTWEIGHT_BOLD)
            return police
        except Exception:
            return self.GetFont()

    def OnSelection(self, event):
        self.selection = event.GetSelection() 
        event.Skip() 

    def SetDonnees(self, donnees):
        self.donnees = donnees
        listeLabels = []
        for donnee in self.donnees :
            listeLabels.append(donnee["label"])
        self.SetItems(listeLabels)
    
    def GetSelection2(self):
        return self.selection
    
    def SetSelection2(self, index=None):
        if index != None :
            self.Select(index)
            self.selection = index
        
    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            # painting the control, but there is no valid item selected yet
            self.selection = None
            return

        r = wx.Rect(*rect)  # make a copy
        r.Deflate(5, 5)
        
        if len(self.donnees) > 0 :
            dictItem = self.donnees[item]
            if flags & ODCB_PAINTING_CONTROL:
                # for painting the control itself
                self.selection = item
                self.DessineItemActif(dc, r, dictItem, flags)
            else:
                # for painting the items in the popup
                self.DessineItem(dc, r, dictItem, flags)
           
    def DessineItemActif(self, dc, r, dictItem, flags=0):
        """ Dessine le contrôle """        
        self.DessineItem(dc, r, dictItem, flags)
        
    def DessineItem(self, dc, r, dictItem, flags=0):
        """ Dessine un item dans la liste popup """
        sombre = UTILS_Interface.EstSombre()
        selectionne = bool(flags & ODCB_PAINTING_SELECTED)
        # Quand la plateforme dessine la sélection, on conserve sa couleur de
        # texte native. Sinon, les deux niveaux typographiques suivent les rôles
        # du design system.
        texte_natif = dc.GetTextForeground()
        texte_principal = texte_natif if selectionne else UTILS_Interface.GetCouleurRole("on_surface", sombre=sombre)
        texte_secondaire = texte_natif if selectionne else UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=sombre)

        # Image
        if ("image" in dictItem) == False or dictItem["image"] == None :
            tailleImage = (0, 0)
        else :
            tailleImage = dictItem["image"].GetSize()
            dc.DrawBitmap(dictItem["image"], int(r.x), int((r.y + 0) + ( (r.height/2) - dc.GetCharHeight() )/2))
        
        # Dessin du label
        dc.SetTextForeground(texte_principal)
        dc.SetFont(self._Police(1.05, gras=True))
        hauteur_label = dc.GetCharHeight()
        dc.DrawText(dictItem["label"], int(r.x + tailleImage[0] + 4), int(r.y + max(0, (r.height / 2 - hauteur_label) / 2)))
        
        # Dessin de la description
        description = dictItem["description"]
        dc.SetTextForeground(texte_secondaire)
        dc.SetFont(self._Police(0.82, gras=False))
        largeur = r.width - tailleImage[0] - 4
        description = wordwrap.wordwrap(description, largeur, dc)
        if self.wrap == False :
            if "\n" in description :
                description = u"%s..." % description[0:description.index("\n")-1]
            y_description = r.y + max(hauteur_label + 3, int(r.height / 2))
            dc.DrawText(description, int(r.x + tailleImage[0] + 4), int(y_description))
        else :
            y_description = r.y + max(hauteur_label + 3, int(r.height / 2))
            dc.DrawLabel(description, wx.Rect(int(r.x + tailleImage[0] + 4), int(y_description), int(r.width - tailleImage[0]), int(max(14, r.height - (y_description - r.y)))))
        
    
    def OnDrawBackground(self, dc, rect, item, flags):
        # Sélection et contrôle fermé : conserver le rendu natif de la
        # plateforme. Les lignes du popup reçoivent simplement une alternance
        # sémantique discrète, claire comme sombre.
        if flags & (ODCB_PAINTING_CONTROL | ODCB_PAINTING_SELECTED):
            OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return

        sombre = UTILS_Interface.EstSombre()
        role = "surface_container_lowest" if item % 2 == 0 else "surface_container_low"
        bgCol = UTILS_Interface.GetCouleurRole(role, sombre=sombre)
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        if 'phoenix' in wx.PlatformInfo:
            dc.DrawRectangle(rect)
        else :
            dc.DrawRectangleRect(rect)

    # Overridden from OwnerDrawnComboBox, should return the height
    # needed to display an item in the popup, or -1 for default
    def OnMeasureItem(self, item):
        return self.hauteurItem

    # Overridden from OwnerDrawnComboBox.  Callback for item width, or
    # -1 for default/undetermined
    def OnMeasureItemWidth(self, item):
        return -1; # default - will be measured from text width
    

        

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        donnees = [
            {"image" : wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_ANY), "label" : _(u"Item 1"), "description" : _(u"Ceci est la description de l'item 1 qui est vraiment un texte très long qui devrait normalement dnépasser.")} ,
            {"image" : wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_ANY), "label" : _(u"Item 2"), "description" : _(u"Ceci est la description de l'item 2")} ,
            {"image" : None, "label" : _(u"Item 3"), "description" : _(u"Ceci est la description de l'item 3")} ,
            {"label" : _(u"Item 4"), "description" : _(u"Ceci est la description de l'item 4")} ,
            ]
        self.ctrl1 = CTRL(panel, donnees=donnees, nbreLignesDescription=1)
        self.ctrl1.Select(0)
        
        donnees = []
        for x in range(1, 100) :
            donnees.append({"image" : wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Loupe.png"), wx.BITMAP_TYPE_ANY), "label" : _(u"Item %d") % x, "description" : _(u"Ceci est la description de l'item %d") % x})
        self.ctrl2 = CTRL(panel, donnees=donnees)
##        self.ctrl2.Select(0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl1, 0, wx.ALL | wx.EXPAND, 10)
        sizer_2.Add(self.ctrl2, 0, wx.ALL | wx.EXPAND, 10)
        panel.SetSizer(sizer_2)
        self.Layout()
        
        self.Bind(wx.EVT_COMBOBOX, self.OnSelection2, self.ctrl2)

    def OnSelection2(self, event):
        print("Selection =", self.ctrl2.GetSelection2()) 
        


if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
