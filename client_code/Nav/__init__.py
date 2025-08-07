from ._anvil_designer import NavTemplate
from anvil import *
import anvil.server

from .. PartRecords import PartRecords
from .. VendorRecords import VendorRecords
from .. PurchaseOrderRecords import PurchaseOrderRecords
from .. InventoryRecords import InventoryRecords
from .. InventoryBins import InventoryBins
from .. InventoryStatusJournal import InventoryStatusJournal
from .. InventoryBinsJournal import InventoryBinsJournal
from .. TestTools import TestTools

class Nav(NavTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.menu_items = [
      {"title": "Parts", "form_class": PartRecords},
      {"title": "Vendors", "form_class": VendorRecords},
      {"title": "PurchaseOrders", "form_class": PurchaseOrderRecords},
      {"title": "InventoryRecords", "form_class": InventoryRecords},
      {"title": "InventoryBins", "form_class": InventoryBins},
      {"title": "InventoryStatusJournal", "form_class": InventoryStatusJournal},
      {"title": "InventoryBinsJournal", "form_class": InventoryBinsJournal},
      {"title": "TestTools", "form_class": TestTools},      
    ]
    self.menu_panel.items = self.menu_items
    self.menu_panel.set_event_handler('x-load-form', self.load_form_event)
    self.load_form("Parts", PartRecords)  # Default view

  def load_form_event(self, **event_args):
    self.load_form(event_args['title'], event_args['form_class'])

  def load_form(self, title, form_class):
    self.content_panel.clear()
    self.content_panel.add_component(form_class())
