from ._anvil_designer import NavTemplate
from anvil import *
import anvil.server

from .. PartRecords import PartRecords
from .. VendorRecords import VendorRecords
#from ..DesignBOMBrowser import DesignBOMBrowser

class Nav(NavTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.menu_items = [
      {"title": "Parts", "form_class": PartRecords},
      {"title": "Vendors", "form_class": VendorRecords},
    ]
    self.menu_panel.items = self.menu_items
    self.menu_panel.set_event_handler('x-load-form', self.load_form_event)
    self.load_form("Parts", PartRecords)  # Default view

  def load_form_event(self, **event_args):
    self.load_form(event_args['title'], event_args['form_class'])

  def load_form(self, title, form_class):
    self.content_panel.clear()
    self.content_panel.add_component(form_class())
