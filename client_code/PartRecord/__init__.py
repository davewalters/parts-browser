# PartRecord Form - detail view and editing of a part

from anvil import *
import anvil.server
from ._anvil_designer import PartRecordTemplate
from datetime import datetime
from .. import config
from .. import PartVendorRecords
from .. DesignBOMRecord import DesignBOMRecord

class PartRecord(PartRecordTemplate):
  def __init__(self, part, prev_filter_part="", prev_filter_desc="", prev_filter_type="", prev_filter_status="", **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_vendor_list.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.button_BOM.role = "new-button"

    self.part = part or {}
    self.is_new = part is None
    self.button_delete.visible = not self.is_new
    self.button_BOM.visible = self.part.get("type") == "assembly"

    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status

    # Dropdown options
    self.drop_down_status.items = ["active", "obsolete"]
    self.drop_down_type.items = ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_unit.items = ["each", "per m", "per hr", "multiple"]
    self.drop_down_process.items = ["machine", "3DP", "assemble", "laser-cut", "weld", "cut-bend", "waterjet-cut", "-"]

    if not self.is_new:
      self.text_box_id.text = part.get("_id", "")
      self.text_box_rev.text = part.get("revision", "")
      self.text_box_desc.text = part.get("description", "")
      self.drop_down_status.selected_value = part.get("status", "active")
      self.text_box_vendor.text = part.get("default_vendor", "")
      self.drop_down_type.selected_value = part.get("type", "part")
      self.drop_down_process.selected_value = part.get("process", "-")
      self.text_box_material.text = part.get("material_spec", "")
      self.drop_down_unit.selected_value = part.get("unit", "each")

      # Prefer rolled-up cost if present
      latest_cost = part.get("latest_cost", {})
      if latest_cost:
        self.text_box_cost.text = str(latest_cost.get("cost_nz", ""))
        self.text_box_cost_date.text = latest_cost.get("cost_date", "")
      else:
        # Fallback: vendor cost
        vendor_id = part.get("default_vendor", "")
        active_vendor = next((v for v in part.get("vendor_part_numbers", []) if v.get("vendor_id") == vendor_id), {})
        self.text_box_cost.text = str(active_vendor.get("cost_$NZ", ""))
        self.text_box_cost_date.text = active_vendor.get("cost_date", "")

    else:
      # New part defaults
      self.text_box_id.text = ""
      self.text_box_rev.text = "A"
      self.text_box_cost.text = "0.00"
      self.text_box_cost_date.text = datetime.today().date().isoformat()
      self.drop_down_status.selected_value = "active"
      self.drop_down_type.selected_value = "part"
      self.drop_down_unit.selected_value = "each"
      self.text_box_vendor.text = "DESIGNATWORK"

  def button_save_click(self, **event_args):
    try:
      latest_cost = {
        "cost_nz": float(self.text_box_cost.text or 0),
        "cost_date": self.text_box_cost_date.text.strip() or "1970-01-01"
      }

      new_data = {
        "_id": self.text_box_id.text,
        "description": self.text_box_desc.text,
        "revision": self.text_box_rev.text,
        "status": self.drop_down_status.selected_value,
        "default_vendor": self.text_box_vendor.text,
        "type": self.drop_down_type.selected_value,
        "process": self.drop_down_process.selected_value,
        "material_spec": self.text_box_material.text,
        "unit": self.drop_down_unit.selected_value,
        "latest_cost": latest_cost,
        "group_code": self.part.get("group_code", ""),
        "root_serial": self.part.get("root_serial", ""),
        "variant": self.part.get("variant", ""),
        "vendor_part_numbers": self.part.get("vendor_part_numbers", [])
      }

      validated = anvil.server.call("save_part_from_client", new_data)
      self.part = validated  # refresh the in-memory copy

      Notification("✅ Part saved.", style="success").show()
      open_form("PartRecords", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  def button_back_click(self, **event_args):
    open_form("PartRecords",
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc,
              filter_type=self.prev_filter_type,
              filter_status=self.prev_filter_status)

  def button_delete_click(self, **event_args):
    part_id = self.text_box_id.text
    if confirm(f"Are you sure you want to delete part '{part_id}'?"):
      try:
        response = anvil.server.call("delete_part", part_id)
        if response.get("deleted_count", 0) == 1:
          Notification("🗑️ Part deleted.", style="danger").show()
        else:
          Notification(f"⚠️ Part '{part_id}' not found.", style="warning").show()
        open_form("PartRecords", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)
      except Exception as e:
        Notification(f"❌ Delete failed: {e}", style="danger").show()

  def button_vendor_list_click(self, **event_args):
    open_form("PartVendorRecords", 
              part=self.part,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc,
              filter_type=self.prev_filter_type,
              filter_status=self.prev_filter_status)

  def button_BOM_click(self, **event_args):
    open_form(DesignBOMRecord(assembly_part_id=self.text_box_id.text))


