from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordTemplate
from datetime import datetime, date

class PartVendorRecord(PartVendorRecordTemplate):
  def __init__(self, part_id,
               vendor_data=None,
               prev_filter_part="", 
               prev_filter_desc="", 
               prev_filter_type="", 
               prev_filter_status="",
               prev_filter_designbom=False,
               back_to_bom=False,
               assembly_part_id=None,
               **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete_vendor.role = "delete-button"

    self.part = anvil.server.call("get_part", part_id)
    self.vendor_data = vendor_data or {
      "vendor_id": "",
      "vendor_part_no": "",
      "vendor_currency": "NZD",
      "vendor_price": 0.0,
      "cost_$NZ": 0.0,
      "cost_date": datetime.today().date().isoformat()
    }

    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom
    self.back_to_bom = back_to_bom
    self.assembly_part_id = assembly_part_id or self.part.get("_id", "")

    try:
      vendor_list = anvil.server.call("get_all_vendors")
      self.drop_down_vendor_id.items = [
        (vendor.get("company_name", vendor["_id"]), vendor["_id"])
        for vendor in vendor_list
      ]
    except Exception as e:
      Notification(f"⚠️ Could not load vendor list: {e}", style="warning").show()
      self.drop_down_vendor_id.items = []

    self.drop_down_vendor_currency.items = ["NZD", "USD", "AU", "EUR", "STG", "SGD"]

    is_active = self.vendor_data.get("vendor_id") == self.part.get("default_vendor", "")
    self.button_delete_vendor.visible = not is_active

    self.label_id.text = self.part.get("_id", "")
    self.label_id.role = "label-border"
    self.drop_down_vendor_id.selected_value = self.vendor_data["vendor_id"]
    self.text_box_vendor_part_no.text = self.vendor_data["vendor_part_no"]
    self.drop_down_vendor_currency.selected_value = self.vendor_data["vendor_currency"]
    self.text_box_vendor_price.text = str(self.vendor_data["vendor_price"])
    self.label_cost_date.text = self.format_date(self.vendor_data["cost_date"])
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"

    self.text_box_vendor_price.set_event_handler("change", self.text_box_vendor_price_change)
    self.drop_down_vendor_currency.set_event_handler("change", self.drop_down_currency_change)

    self.update_cost_nz()

  def get_exchange_rate(self, currency):
    rates = {"NZD": 1.0, "USD": 1.65, "AU": 1.08, "EUR": 1.94, "STG": 2.25, "SGD": 1.29}
    return rates.get(currency, 1.0)

  def update_cost_nz(self):
    try:
      price = float(self.text_box_vendor_price.text)
      rate = self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)
      cost_nz = round(price * rate, 2)
      self.vendor_data["cost_$NZ"] = cost_nz
      self.vendor_data["cost_date"] = datetime.today().date()
      self.label_cost_nz.text = self.format_currency(cost_nz)
      self.label_cost_date.text = self.format_date(self.vendor_data["cost_date"])
    except:
      self.label_cost_nz.text = "Invalid price"

  def drop_down_currency_change(self, **event_args):
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"
    self.update_cost_nz()

  def text_box_vendor_price_change(self, **event_args):
    self.update_cost_nz()

  def button_save_click(self, **event_args):
    self.vendor_data.update({
      "vendor_id": self.drop_down_vendor_id.selected_value,
      "vendor_part_no": self.text_box_vendor_part_no.text,
      "vendor_currency": self.drop_down_vendor_currency.selected_value,
      "vendor_price": float(self.text_box_vendor_price.text),
      # Do not overwrite cost_date here — already set correctly in update_cost_nz()
    })

    if self.part.get("default_vendor") != self.vendor_data["vendor_id"]:
      self.part["default_vendor"] = self.vendor_data["vendor_id"]

    rate = self.get_exchange_rate(self.vendor_data["vendor_currency"])
    self.vendor_data["cost_$NZ"] = round(self.vendor_data["vendor_price"] * rate, 2)

    updated = False
    for idx, vendor in enumerate(self.part["vendor_part_numbers"]):
      if vendor["vendor_id"] == self.vendor_data["vendor_id"]:
        self.part["vendor_part_numbers"][idx] = self.vendor_data
        updated = True
        break

    if not updated:
      self.part["vendor_part_numbers"].append(self.vendor_data)

    self.part["latest_cost"] = {
      "cost_nz": self.vendor_data["cost_$NZ"],
      "cost_date": self.vendor_data["cost_date"]  # Should already be a date object
    }

    try:
      for v in self.part["vendor_part_numbers"]:
        v.pop("vendor_company_name", None)
        v.pop("is_active", None)

      validated = anvil.server.call("save_part_from_client", self.part)
      Notification("✅ Vendor details and part cost saved.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to save vendor: {e}", style="danger", timeout=None).show()


  def button_back_click(self, **event_args):
    if self.back_to_bom:
      open_form("DesignBOMRecord",
                assembly_part_id=self.assembly_part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)
    else:
      open_form("PartVendorRecords",
                part_id=self.part.get("_id", ""),
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)

  def button_delete_vendor_click(self, **event_args):
    vendor_id = self.vendor_data.get("vendor_id", "")
    if not vendor_id:
      Notification("⚠️ No vendor selected for deletion.", style="warning").show()
      return

    if not confirm(f"Are you sure you want to delete vendor '{vendor_id}' from this part?"):
      return

    self.part["vendor_part_numbers"] = [
      v for v in self.part.get("vendor_part_numbers", [])
      if v.get("vendor_id") != vendor_id
    ]

    try:
      validated = anvil.server.call("save_part_from_client", self.part)
      Notification(f"🗑️ Vendor '{vendor_id}' deleted.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to delete vendor: {e}", style="danger").show()

    self.button_back_click()

  def format_date(self, date_input):
    if isinstance(date_input, datetime):
      return date_input.date().isoformat()
    elif isinstance(date_input, date):
      return date_input.isoformat()
    elif isinstance(date_input, str):
      return date_input.split("T")[0] if "T" in date_input else date_input
    return "1970-01-01"

  def format_currency(self, value):
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"










