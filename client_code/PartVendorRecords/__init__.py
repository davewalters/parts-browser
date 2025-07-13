from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordsTemplate
from .. import PartVendorRecord
from .. import PartRecord

class PartVendorRecords(PartVendorRecordsTemplate):
  def __init__(self, part, filter_part="", filter_desc="", **kwargs):
    self.init_components(**kwargs)
    self.button_new_vendor.role = "save-button"
    self.button_cancel.role = "mydefault-button"
    self.part = part
    self.vendor_lookup = self.get_vendor_lookup()
    self.prev_filter_part = filter_part
    self.prev_filter_desc = filter_desc
    self.label_id.text = part.get("_id", "")
    self.label_id.role = "label-border"

    default_vendor = self.part.get("default_vendor", "")
    self.vendor_data = []

    for vendor in self.part.get("vendor_part_numbers", []):
      v = vendor.copy()
      v["vendor_company_name"] = self.vendor_lookup.get(v.get("vendor_id"), v.get("vendor_id"))
      v["is_active"] = v.get("vendor_id") == default_vendor
      self.vendor_data.append(v)

    self.repeating_panel_1.items = self.vendor_data
    self.repeating_panel_1.set_event_handler("x-set-default-vendor", self.set_active_vendor)
    self.repeating_panel_1.set_event_handler("x-edit-vendor", self.edit_vendor)

  def get_vendor_lookup(self):
    try:
      vendor_list = anvil.server.call("get_all_vendors")
      return {
        vendor.get("_id"): vendor.get("company_name", vendor["_id"])
        for vendor in vendor_list
      }
    except Exception as e:
      Notification(f"⚠️ Could not load vendor names: {e}", style="warning").show()
      return {}

  def button_cancel_click(self, **event_args):
    open_form("PartRecord",
              part=self.part,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc)

  def button_new_vendor_click(self, **event_args):
    open_form("PartVendorRecord",
              part=self.part,
              vendor_data=None,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc)

  def set_active_vendor(self, vendor_id, **event_args):
    self.part["default_vendor"] = vendor_id

    for item in self.vendor_data:
      item["is_active"] = item.get("vendor_id") == vendor_id

    self.repeating_panel_1.items = self.vendor_data

    try:
      # Replace full part record with validated version
      validated = anvil.server.call("save_part_from_client", self.part)
      Notification(f"✅ '{vendor_id}' set as default vendor.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to update default vendor: {e}", style="danger").show()

  def edit_vendor(self, vendor_data, **event_args):
    open_form("PartVendorRecord",
              part=self.part,
              vendor_data=vendor_data,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc)


