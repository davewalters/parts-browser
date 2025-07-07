# V.ItemTemplate3 - handles individual vendor rows

from anvil import *
from ._anvil_designer import ItemTemplate3Template
from .. import PartVendorRecords
from .. import PartVendorRecord

class ItemTemplate3(ItemTemplate3Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.radio_button_active_vendor.group_name = "vendor_active_group"
    self.radio_button_active_vendor.set_event_handler("change", self.radio_button_active_vendor_change)

    self.label_vendor_id.text = self.item.get("vendor_company_name", "")
    self.label_vendor_part_no.text = self.item.get("vendor_part_no", "")
    self.label_vendor_currency.text = self.item.get("vendor_currency", "")
    self.label_vendor_price.text = str(self.item.get("vendor_price", ""))
    self.label_cost_NZD.text = str(self.item.get("cost_$NZ", ""))
    self.label_cost_date.text = self.item.get("cost_date", "")

    is_active = self.item.get("is_active", False)
    color = "#000" if is_active else "#aaa"  # grey out inactive
    
    for lbl in [self.label_vendor_id, self.label_vendor_part_no,
                self.label_vendor_currency, self.label_vendor_price, 
                self.label_cost_NZD, self.label_cost_date]:
      lbl.foreground = color

    self.radio_button_active_vendor.selected = is_active

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-edit-vendor", vendor_data=self.item)

  def radio_button_active_vendor_change(self, **event_args):
    if self.radio_button_active_vendor.selected:
      self.parent.raise_event("x-set-default-vendor", vendor_id=self.item.get("vendor_id"))

