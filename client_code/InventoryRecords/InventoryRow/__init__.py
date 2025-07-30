from ._anvil_designer import InventoryRowTemplate
from anvil import *

class InventoryRow(InventoryRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_view.set_event_handler("click", self.view_button_click)

  def view_button_click(self, **event_args):
    self.raise_event("x-show-detail", inventory_row=self.item)

