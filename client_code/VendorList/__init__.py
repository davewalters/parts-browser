# VendorList Form - List and manage vendors for a part

from anvil import *
from ._anvil_designer import VendorListTemplate
import anvil.http
import json

class VendorList(VendorListTemplate):
  def __init__(self, part, **kwargs):
    self.init_components(**kwargs)
    self.part = part
    self.label_part_id.text = part.get("_id", "")
    self.repeating_panel_vendors.items = part.get("vendor_part_numbers", [])

  def button_new_vendor_click(self, **event_args):
    open_form("VendorDetails", part=self.part, vendor_data=None)

  def set_default_vendor(self, vendor_id, cost_nz, cost_date):
    self.part["default_vendor"] = vendor_id
    self.part["latest_cost"] = {"cost_nz": cost_nz, "cost_date": cost_date}
    # Save part to FastAPI
    anvil.http.request(
      url=f"http://127.0.0.1:8000/parts/{self.part['_id']}",
      method="PUT",
      data=json.dumps(self.part),
      headers={"Content-Type": "application/json"}
    )
    Notification(f"✅ Set {vendor_id} as default vendor.", style="success").show()
