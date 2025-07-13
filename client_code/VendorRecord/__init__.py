from anvil import *
import anvil.server
from ._anvil_designer import VendorRecordTemplate
from datetime import datetime

class VendorRecord(VendorRecordTemplate):
  def __init__(self, vendor, prev_filter_vendor_id="", prev_filter_company_name="", **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.vendor = vendor
    self.is_new = vendor is None
    self.button_delete.visible = not self.is_new
    self.prev_filter_vendor_id = prev_filter_vendor_id
    self.prev_filter_company_name = prev_filter_company_name

    self.drop_down_status.items = ["active", "obsolete"]

    if self.vendor:
      address = self.vendor.get("address", {})
      contact = self.vendor.get("contact", {})
      self.text_box_id.text = self.vendor.get("_id", "")
      self.text_box_company_name.text = self.vendor.get("company_name", "")
      self.drop_down_status.selected_value = self.vendor.get("status", "active")

      self.text_box_address_line1.text = address.get("line1", "")
      self.text_box_address_line2.text = address.get("line2", "")
      self.text_box_city.text = address.get("city", "")
      self.text_box_postal_code.text = address.get("postal_code", "")
      self.text_box_state.text = address.get("state", "")
      self.text_box_country.text = address.get("country", "")

      self.text_box_contact_name.text = contact.get("name", "")
      self.text_box_phone.text = contact.get("phone", "")
      self.text_box_email.text = contact.get("email", "")

      self.text_area_categories.text = ", ".join(self.vendor.get("categories", []))

    else:
      self.drop_down_status.selected_value = "active"

  def button_save_click(self, **event_args):
    new_address = {
      "line1": self.text_box_address_line1.text or "",
      "line2": self.text_box_address_line2.text or "",
      "city": self.text_box_city.text or "",
      "state": self.text_box_state.text or "",
      "postal_code": self.text_box_postal_code.text or "",
      "country": self.text_box_country.text or "",
    }

    new_contact = {
      "name": self.text_box_contact_name.text or "",
      "phone": self.text_box_phone.text or "",
      "email": self.text_box_email.text or "",
    }

    new_data = {
      "_id": self.text_box_id.text,
      "status": self.drop_down_status.selected_value or "active",
      "company_name": self.text_box_company_name.text or "",
      "address": new_address,
      "contact": new_contact,
      "categories": [c.strip() for c in self.text_area_categories.text.split(",") if c.strip()]
    }

    try:
      validated = anvil.server.call("save_vendor_from_client", new_data)
      Notification("✅ Vendor saved.").show()
      open_form("VendorRecords",
                filter_vendor_id=self.prev_filter_vendor_id,
                filter_company_name=self.prev_filter_company_name)
    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  def button_back_click(self, **event_args):
    open_form("VendorRecords", 
              filter_vendor_id=self.prev_filter_vendor_id,
              filter_company_name=self.prev_filter_company_name)

  def button_delete_click(self, **event_args):
    vendor_id = self.text_box_id.text
    confirmed = confirm(f"Are you sure you want to delete vendor '{vendor_id}'?")
    if not confirmed:
      return
    try:
      result = anvil.server.call("delete_vendor", vendor_id)
      Notification("🗑️ Vendor deleted.", style="danger").show()
      open_form("VendorRecords",
                filter_vendor_id=self.prev_filter_vendor_id,
                filter_company_name=self.prev_filter_company_name)
    except Exception as e:
      Notification(f"❌ Delete failed: {e}", style="danger").show()

