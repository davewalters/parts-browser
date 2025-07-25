from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordsTemplate
from datetime import datetime
from ..PartVendorRecord import PartVendorRecord

class PartVendorRecords(PartVendorRecordsTemplate):
  def __init__(self, part_id,
               prev_filter_part="",
               prev_filter_desc="",
               prev_filter_type="",
               prev_filter_status="",
               prev_filter_designbom=False,
               back_to_bom=False,
               back_to_po=False,
               assembly_part_id=None,
               purchase_order_id=None,
               **kwargs):

    self.init_components(**kwargs)
    self.button_new_vendor.role = "new-button"
    self.button_cancel.role = "mydefault-button"
    self.button_back_to_bom.role = "mydefault-button"
    self.button_back_to_po.role = "mydefault-button"

    print(f"part_id = {part_id}")
    self.part = anvil.server.call("get_part", part_id)
    s_part_id = self.part.get("_id", "")
    print(f"self.part.get_id: {s_part_id}")
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom
    self.back_to_bom = back_to_bom
    self.button_back_to_bom.visible = self.back_to_bom
    self.back_to_po = back_to_po
    self.button_back_to_po.visible = self.back_to_po
    self.assembly_part_id = assembly_part_id or self.part.get("_id", "")
    
    self.label_id.text = self.part.get("_id", "")
    self.label_id.role = "label-border"
    self.vendor_lookup = self.get_vendor_lookup()

    default_vendor = self.part.get("default_vendor", "")
    if default_vendor and not self.part.get("vendor_part_numbers"):
      company_name = self.vendor_lookup.get(default_vendor, default_vendor)
      default_entry = {
        "vendor_id": default_vendor,
        "vendor_part_no": self.part.get("_id", ""),
        "vendor_currency": "NZD",
        "vendor_price": 0.0,                   
        "cost_$NZ": 0.0,
        "cost_date": datetime.today().date(),
        "vendor_company_name": company_name
      }

      self.part["vendor_part_numbers"] = [default_entry]
    
      try:
        # Remove UI-only fields before sending to schema validator
        for v in self.part["vendor_part_numbers"]:
          v.pop("vendor_company_name", None)
        anvil.server.call("save_part_from_client", self.part)
        Notification(f"✅ Default vendor '{company_name}' added.", style="success").show()
      except Exception as e:
        Notification(f"❌ Could not save default vendor: {e}", style="danger", timeout=None).show()
    
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
    if self.back_to_po:
      open_form("PurchaseOrderRecord", purchase_order_id=self.purchase_order_id)
    return
    if self.back_to_bom:
      open_form("DesignBOMRecord",
                assembly_part_id=self.assembly_part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)
    else:
      open_form("PartRecord",
                part_id=self.part.get("_id", ""),
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)

  def button_back_to_bom_click(self, **event_args):
    self.button_cancel_click()

  def button_back_to_po_click(self, **event_args):
    open_form("PurchaseOrderRecord", purchase_order_id=self.purchase_order_id)  

  def button_new_vendor_click(self, **event_args):
    open_form("PartVendorRecord",
              part_id=self.part.get("_id", ""),
              vendor_data=None,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status,
              prev_filter_designbom=self.prev_filter_designbom,
              back_to_bom=self.back_to_bom,
              assembly_part_id=self.assembly_part_id)

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
              part_id=self.part.get("_id", ""),
              vendor_data=vendor_data,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status,
              prev_filter_designbom=self.prev_filter_designbom,
              back_to_bom=self.back_to_bom,
              assembly_part_id=self.assembly_part_id)








