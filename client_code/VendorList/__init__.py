# VendorList Form - List and manage vendors for a part

from anvil import *
from ._anvil_designer import VendorListTemplate
import anvil.http
import json

class VendorList(VendorListTemplate):
  def __init__(self, part, **kwargs):
    self.init_components(**kwargs)
    self.part = part
    self.repeating_panel_1.items = self.part.get("vendor_part_numbers", [])
    self.label_part_id.text = self.part.get("_id", "")

  def button_back_click(self, **event_args):
    open_form("PartDetail")

  def button_new_vendor_click(self, **event_args):
    open_form("VendorDetails", part_id=self.part_id, vendor=None)

  def set_active_vendor(self, selected_vendor_id):
    for vendor in self.vendor_data:
      vendor["is_active"] = vendor["vendor_id"] == selected_vendor_id

    self.repeating_panel_1.items = self.vendor_data
    Notification(f"✅ Set '{selected_vendor_id}' as default vendor.", style="success").show()
