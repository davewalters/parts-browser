# V.ItemTemplate3 - handles individual vendor rows

from anvil import *
from ._anvil_designer import ItemTemplate3Template
from .. import VendorList
from .. import VendorDetails

class ItemTemplate3(ItemTemplate3Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.label_vendor_id.text = self.item.get("vendor_id", "")
    self.label_vendor_part_no.text = self.item.get("vendor_part_no", "")
    self.label_vendor_currency.text = self.item.get("vendor_currency", "")
    self.label_cost_NZD.text = str(self.item.get("cost_$NZ", ""))
    self.label_cost_date.text = self.item.get("cost_date", "")
    self.radio_button_active_vendor.selected = self.item.get("is_active", False)

  def button_view_click(self, **event_args):
    open_form("VendorDetails", part=self.item.get("_part"), vendor_data=self.item)

  def radio_button_active_vendor_change(self, **event_args):
    if self.radio_button_active_vendor.selected:
      self.parent.raise_event("x-set-default-vendor", vendor_id=self.item.get("vendor_id"))

