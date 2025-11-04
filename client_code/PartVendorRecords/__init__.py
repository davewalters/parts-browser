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
               return_to: dict | None = None,
               **kwargs):

    self.init_components(**kwargs)
    self._return_to = return_to or None
    self.button_new_vendor.role = "new-button"
    self.button_cancel.role = "mydefault-button"
    self.button_back_to_bom.role = "mydefault-button"
    self.button_back_to_po.role = "mydefault-button"
    
    # Load the part
    self.part = anvil.server.call("get_part", part_id)
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom

    self.back_to_bom = back_to_bom
    self.button_back_to_bom.visible = self.back_to_bom
    self.back_to_po = back_to_po
    self.button_back_to_po.visible = self.back_to_po
    self.purchase_order_id = purchase_order_id
    self.assembly_part_id = assembly_part_id or self.part.get("_id", "")

    self.label_id.text = self.part.get("_id", "")
    self.label_id.role = "label-border"

    # Build vendor lookup once (vendor_id -> company_name)
    self.vendor_lookup = self._build_vendor_lookup()

    # If we have a default_vendor but no vendor_part_numbers yet, seed one row
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
        # UI-only helper:
        "vendor_company_name": company_name,
      }
      self.part["vendor_part_numbers"] = [default_entry]

      try:
        # Strip UI fields before saving
        for v in self.part["vendor_part_numbers"]:
          v.pop("vendor_company_name", None)
        anvil.server.call("save_part_from_client", self.part)
        Notification(f"✅ Default vendor '{company_name}' added.", style="success").show()
      except Exception as e:
        Notification(f"❌ Could not save default vendor: {e}", style="danger", timeout=None).show()

    self._load_vendor_rows()

  # --- helpers ---
  def _go_back(self):
    if self._return_to:
      try:
        form_name = self._return_to.get("form") or "PartRecords"
        kwargs = dict(self._return_to.get("kwargs") or {})
        return_filters = self._return_to.get("filters")
        open_form(form_name, **kwargs, return_filters=return_filters)
        return
      except Exception as ex:
        Notification(f"Back navigation failed: {ex}", style="warning").show()
    
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
        
  def _build_vendor_lookup(self) -> dict:
    """
    Returns { vendor_id: company_name }
    Uses get_all_vendors() which should return docs containing 'vendor_id' and 'company_name'.
    """
    try:
      vendor_list = anvil.server.call("get_all_vendors") or []
      # IMPORTANT: key by 'vendor_id', not '_id'
      return {
        v.get("vendor_id"): (v.get("company_name") or v.get("vendor_id"))
        for v in vendor_list
        if v.get("vendor_id")
      }
    except Exception as e:
      Notification(f"⚠️ Could not load vendor names: {e}", style="warning").show()
      return {}

  def _load_vendor_rows(self):
    default_vendor = self.part.get("default_vendor", "")
    self.vendor_data = []

    for vendor in self.part.get("vendor_part_numbers", []) or []:
      v = dict(vendor)  # shallow copy
      vid = v.get("vendor_id", "")
      v["vendor_company_name"] = self.vendor_lookup.get(vid, vid)
      v["is_active"] = (vid == default_vendor)
      self.vendor_data.append(v)

    self.repeating_panel_1.items = self.vendor_data
    self.repeating_panel_1.set_event_handler("x-set-default-vendor", self.set_active_vendor)
    self.repeating_panel_1.set_event_handler("x-edit-vendor", self.edit_vendor)

  # --- navigation ---
  def _make_child_return_to(self):
  # Prefer returning to THIS list view, otherwise fall back to upstream
    return self._return_to or {
    "form": "PartVendorRecords",
    "kwargs": {
      "part_id": self.part.get("_id", ""),
      "prev_filter_part": self.prev_filter_part,
      "prev_filter_desc": self.prev_filter_desc,
      "prev_filter_type": self.prev_filter_type,
      "prev_filter_status": self.prev_filter_status,
      "prev_filter_designbom": self.prev_filter_designbom,
      "back_to_bom": self.back_to_bom,
      "back_to_po": self.back_to_po,
      "assembly_part_id": self.assembly_part_id,
      "purchase_order_id": self.purchase_order_id,
      "return_to": self._return_to,   # keep the upstream chain intact
    }
  }

  def button_cancel_click(self, **event_args):
    self._go_back()

  def button_back_to_bom_click(self, **event_args):
    self._go_back()

  def button_back_to_po_click(self, **event_args):
    self._go_back()

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
              assembly_part_id=self.assembly_part_id,
              return_to=self._return_to)

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
              assembly_part_id=self.assembly_part_id,
              return_to=self._return_to)

  def set_active_vendor(self, vendor_id, **event_args):
    # Update model
    self.part["default_vendor"] = vendor_id

    # Flip the radio buttons flag locally
    for item in self.vendor_data:
      item["is_active"] = (item.get("vendor_id") == vendor_id)
    self.repeating_panel_1.items = self.vendor_data  # refresh rows

    # Persist
    try:
      anvil.server.call("save_part_from_client", self.part)
      company_name = self.vendor_lookup.get(vendor_id, vendor_id)
      Notification(f"✅ '{company_name}' set as default vendor.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to update default vendor: {e}", style="danger").show()

  









