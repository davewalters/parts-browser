# PartDetail Form - detail view and editing of a part

from anvil import *
from ._anvil_designer import PartDetailTemplate
import anvil.http
import json
from datetime import datetime

class PartDetail(PartDetailTemplate):
  def __init__(self, part, prev_filter_part="", prev_filter_desc="", **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "mydefault-button"
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.part = part
    self.is_new = part is None
    self.button_delete.visible = not self.is_new
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc

    # Populate dropdown options
    self.drop_down_status.items = ["active", "obsolete"]
    self.drop_down_type.items = ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_unit.items = ["each", "per m", "per hr", "multiple"]
    self.drop_down_process.items = ["machine", "3DP", "assemble", "laser-cut", "weld", "cut-bend", "waterjet-cut", "-"]
    
    if self.part:
      self.text_box_id.text = part.get("_id", "")
      self.text_box_rev.text = part.get("revision", "")
      self.text_box_desc.text = part.get("description", "")
      self.drop_down_status.selected_value = part.get("status", "active")
      self.text_box_vendor.text = part.get("default_vendor", "")
      self.drop_down_type.selected_value = part.get("type", "part")
      self.drop_down_process.selected_value = part.get("process", "-")
      self.text_box_material.text = part.get("material_spec", "")
      self.drop_down_unit.selected_value = part.get("unit", "each")

      latest = part.get("latest_cost", {})
      self.text_box_cost.text = str(latest.get("cost_nz", ""))
      self.text_box_cost_date.text = latest.get("cost_date", "")
    else:
      # set sensible defaults for new part
      self.text_box_id.text = ""
      self.text_box_rev.text = "A"
      self.drop_down_status.selected_value = "active"
      self.drop_down_type.selected_value = "part"
      self.drop_down_unit.selected_value = "each"
      self.text_box_vendor.text = "DESIGNATWORK"
      self.text_box_cost.text = "0.00"
      self.text_box_cost_date.text = datetime.today().date().isoformat()  # e.g., "2025-06-30"

    


  def button_save_click(self, **event_args):
    try:
      latest_cost = {
        "cost_nz": 0.0,
        "cost_date": "1970-01-01"
      }

      try:
        cost_val = float(self.text_box_cost.text)
        latest_cost["cost_nz"] = cost_val
      except (ValueError, TypeError):
        pass

      try:
        date_text = self.text_box_cost_date.text.strip()
        dt = datetime.fromisoformat(date_text)
        latest_cost["cost_date"] = dt.date().isoformat()
      except Exception:
        pass

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
        "vendor_part_numbers": [
          {
            "vendor_id": self.text_box_vendor.text or "-",
            "vendor_part_no": "-",
            "vendor_currency": "-",
            "vendor_price": 0.0,
            "cost_$NZ": latest_cost["cost_nz"],
            "cost_date": latest_cost["cost_date"]
          }
        ]
      }

      if self.is_new:
        url = "http://127.0.0.1:8000/parts"
        method = "POST"
      else:
        url = f"http://127.0.0.1:8000/parts/{self.part['_id']}"
        method = "PUT"

      json_string = json.dumps(new_data)

      #print("📤 Sending to FastAPI:", new_data)
      #print("📤 Payload repr:", json_string)

      anvil.http.request(
        url=url,
        method=method,
        data=json_string,
        headers={"Content-Type": "application/json"}
      )

      Notification("✅ Part saved.", style="success").show()
      open_form("Form1", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

    except Exception as e:
    # If the error is due to duplicate _id
      if "already exists" in str(e):
        Notification("⚠️ Part ID already exists. Please choose a different ID.", style="warning").show()
      else:
        Notification(f"❌ Save failed: {e}", style="danger").show()


  def button_back_click(self, **event_args):
    open_form("Form1", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

  
  def button_delete_click(self, **event_args):
    part_id = self.text_box_id.text
    confirmed = confirm(f"Are you sure you want to delete part '{part_id}'?")
    if not confirmed:
      return
    try:
      response = anvil.http.request(
        url=f"http://127.0.0.1:8000/parts/{part_id}",
        method="DELETE"
      )
      Notification("🗑️ Part deleted.", style="danger").show()
      open_form("Form1", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)
    except Exception as e:
      Notification(f"❌ Delete failed: {e}", style="danger").show()

