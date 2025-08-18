from anvil import *
import anvil.server
from ._anvil_designer import PartRecordTemplate
from datetime import datetime
from .. import config
from .. PartRecords import PartRecords

class PartRecord(PartRecordTemplate):
  def __init__(self, part_id, 
              prev_filter_part="",
              prev_filter_desc="",
              prev_filter_type="",
              prev_filter_status="",
              prev_filter_designbom=False,
              **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_vendor_list.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.button_BOM.role = "new-button"

    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom
    print(f"In PartRecord: prev_filter_designbom = {prev_filter_designbom}")
    
    self.part = {}
    self.is_new = part_id is None
    if not self.is_new:
      try:
        fetched = anvil.server.call("get_part", part_id)
        if fetched is None:
          Notification(f"⚠️ Part ID '{part_id}' not found in database.", style="warning").show()
        else:
          self.part = fetched
      except Exception as e:
        Notification(f"❌ Failed to load part: {e}", style="danger").show()
    
    self.drop_down_status.items = ["active", "obsolete"]
    self.drop_down_type.items = ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_unit.items = ["each", "per m", "per hr", "multiple"]
    self.drop_down_process.items = ["machine", "3DP", "assemble", "laser-cut", "weld", "cut-bend", "waterjet-cut", "-"]

    self.text_box_id.text = self.part.get("_id", "")
    self.text_box_rev.text = self.part.get("revision", "A")
    self.text_box_desc.text = self.part.get("description", "")
    self.drop_down_status.selected_value = self.part.get("status", "active")
    self.text_box_vendor.text = self.part.get("default_vendor", "DESIGNATWORK")
    self.drop_down_type.selected_value = self.part.get("type", "part")
    self.drop_down_process.selected_value = self.part.get("process", "-")
    self.text_box_material.text = self.part.get("material_spec", "")
    self.drop_down_unit.selected_value = self.part.get("unit", "each")

    latest_cost = self.part.get("latest_cost", {})
    cost_nz = latest_cost.get("cost_nz", 0.0)
    cost_date = latest_cost.get("cost_date", datetime.today().isoformat())
    self.label_cost_nz.text = self.format_currency(cost_nz)
    self.label_date_costed.text = self.format_date(cost_date)
    self.text_box_sell_price_nzd = self.format_currency(self.part.get("sell_price"))

    self.button_delete.visible = bool(self.part)
    self.button_BOM.visible = self.drop_down_type.selected_value == "assembly"

  def button_save_click(self, **event_args):
    try:
      latest_cost = {
        "cost_nz": float(self.label_cost_nz.text.replace("$", "") or 0),
        "cost_date": self.label_date_costed.text.strip() or "1970-01-01"
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
        "vendor_part_numbers": self.part.get("vendor_part_numbers", []),
        "sell_price": self.text_box_sell_price_nzd,
      }

      validated = anvil.server.call("save_part_from_client", new_data)
      self.part = validated

      Notification("✅ Part saved.", style="success").show()
      #get_open_form().content = PartRecords(filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  def button_back_click(self, **event_args):
    open_form("PartRecords",
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc,
              filter_type=self.prev_filter_type,
              filter_status=self.prev_filter_status,
              filter_designbom=self.prev_filter_designbom)
    print(f"In PartRecord opening PartRecords, self.prev_filter_designbom = {self.prev_filter_designbom}")

  def button_delete_click(self, **event_args):
    part_id = self.text_box_id.text
    if confirm(f"Are you sure you want to delete part '{part_id}'?"):
      try:
        response = anvil.server.call("delete_part", part_id)
        if response.get("deleted_count", 0) == 1:
          Notification("🗑️ Part deleted.", style="danger").show()
        else:
          Notification(f"⚠️ Part '{part_id}' not found.", style="warning").show()
        get_open_form().content = PartRecords(filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)
      except Exception as e:
        Notification(f"❌ Delete failed: {e}", style="danger").show()

  def button_vendor_list_click(self, **event_args):
    part_id = self.ensure_part_saved()
    if part_id:
      open_form("PartVendorRecords",
                part_id=part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)
    else:
      print(f"PartRecord->PartVendorRecords: part_id is: {part_id}")

  def button_BOM_click(self, **event_args):
    part_id = self.ensure_part_saved()
    if part_id:
      open_form("DesignBOMRecord",
                assembly_part_id=part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)
    else:
      print(f"PartRecord->DesignBOMRecord: part_id is: {part_id}")

  def format_date(self, iso_string):
    if not iso_string or not isinstance(iso_string, str):
      return "1970-01-01"
    return iso_string.split("T")[0] if "T" in iso_string else iso_string

  def format_currency(self, value):
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"

  def ensure_part_saved(self):
    part_id = self.part.get("_id")
    if not part_id:
      self.button_save_click()
      part_id = self.part.get("_id")
    return part_id




