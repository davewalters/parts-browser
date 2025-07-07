# PartDetail Form - detail view and editing of a part

from anvil import *
from ._anvil_designer import VendorRecordTemplate
import anvil.http
import json
from datetime import datetime
from .. import VendorRecords


class VendorRecord(VendorRecordTemplate):
  def __init__(self, vendor, prev_filter_vendor_id="", prev_filter_company_name="", **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.vendor = vendor
    self.is_new = vender is None
    self.button_delete.visible = not self.is_new
    self.prev_filter_vendor_id = prev_filter_vendor_id
    self.prev_filter_company_name = prev_filter_company_name

    # Populate dropdown options
    self.drop_down_status.items = ["active", "obsolete"]

    vendor = self.item
    address = vendor.get("address", {})
    contact = vendor.get("contact", {})

    if self.vendor:
      self.text_box_id.text = vendor.get("_id", "")
      self.text_box_company_name.text = vendor.get("company_name", "")
      self.drop_down_status.selected_value = vendor.get("status", "active")

      self.text_box_address_line1.text = address.get("line1", "")
      self.text_box_address_line2.text = address.get("line2", "")
      self.text_box_city.text = address.get("city", "")
      self.text_box_postal_code.text = address.get("postal_code", "")
      self.text_box_state.text = address.get("state", "")
      self.text_box_country.text = address.get("country", "")

      self.text_box_contact_name.text = contact.get("name", "")
      self.text_box_phone.text = contact.get("phone", "")
      self.text_box_email.text = contact.get("phone", "")

    else:
      # set sensible defaults for new vendor
      self.drop_down_status.selected_value = "active"


  def button_save_click(self, **event_args):
    new_address = {
      "line1": self.text_box_address_line1.text,
      "line2": self.text_box_address_line2.text,
      "city": self.text_box_city.text,
      "state": self.text_box_state.text,
      "postal_code": self.text_box_postal_code.text,
      "country": self.text_box_country.text,
    }

    new_contact = {
      "name": self.text_box_contact_name.text,
      "phone": self.text_box_phone.text,
      "email": self.text_box_email.text,
    }

    new_data = {
      "_id": self.text_box_id.text,
      "status": self.drop_down_status.selected_value,
      "company_name": self.text_box_company_name.text,
      new_address,
      new_contact,
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
    open_form("PartsList", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

    except Exception as e:
      # If the error is due to duplicate _id
      if "already exists" in str(e):
        Notification("⚠️ Part ID already exists. Please choose a different ID.", style="warning").show()
      else:
        Notification(f"❌ Save failed: {e}", style="danger").show()

  def button_back_click(self, **event_args):
    open_form("PartRecords", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)

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
      open_form("PartsList", filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)
    except Exception as e:
      Notification(f"❌ Delete failed: {e}", style="danger").show()

  def button_vendor_list_click(self, **event_args):
    open_form("PartVendorRecords",
              part=self.part,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc)
