from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordsTemplate
from .. import PartVendorRecord
from .. import PartRecord
from .. import DesignBOMRecord

class PartVendorRecords(PartVendorRecordsTemplate):
  def __init__(self, part, prev_filter_part="", prev_filter_desc="", prev_filter_type="", prev_filter_status="", back_to_bom=False, **kwargs):
    self.init_components(**kwargs)
    self.button_new_vendor.role = "new-button"
    self.button_cancel.role = "mydefault-button"
    self.button_back_to_bom.role = "mydefault-button"

    self.part = part
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.back_to_bom = back_to_bom
    self.button_back_to_bom.visible = self.back_to_bom
    
    self.label_id.text = part.get("_id", "")
    self.label_id.role = "label-border"
    self.vendor_lookup = self.get_vendor_lookup()
    self.load_vendor_data()

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

  def load_vendor_data(self):
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

  def button_cancel_click(self, **event_args):
    if self.back_to_bom:
      open_form("DesignBOMRecord",
                assembly_part_id=self.part["_id"],
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status)
    else:
      open_form("PartRecord",
                part=self.part,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status)

  def button_back_to_bom_click(self, **event_args):
    self.button_cancel_click()

  def button_new_vendor_click(self, **event_args):
    open_form("PartVendorRecord",
              part=self.part,
              vendor_data=None,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)

  def set_active_vendor(self, vendor_id, **event_args):
    self.part["default_vendor"] = vendor_id

    for item in self.vendor_data:
      item["is_active"] = item.get("vendor_id") == vendor_id

    self.repeating_panel_1.items = self.vendor_data

    try:
      validated = anvil.server.call("save_part_from_client", self.part)
      Notification(f"✅ '{vendor_id}' set as default vendor.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to update default vendor: {e}", style="danger").show()

  def edit_vendor(self, vendor_data, **event_args):
    open_form("PartVendorRecord",
              part=self.part,
              vendor_data=vendor_data,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)






