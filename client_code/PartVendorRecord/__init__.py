from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordTemplate
from datetime import datetime
from .. import PartVendorRecords

class PartVendorRecord(PartVendorRecordTemplate):
  def __init__(self, part, vendor_data=None, prev_filter_part="", prev_filter_desc="", prev_filter_type="", prev_filter_status="", **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_cancel.role = "mydefault-button"
    self.button_delete_vendor.role = "delete-button"
    self.text_box_vendor_price.set_event_handler("change", self.text_box_vendor_price_change)
    self.drop_down_vendor_currency.set_event_handler("change", self.drop_down_currency_change)

    self.part = part
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status

    try:
      vendor_list = anvil.server.call("get_all_vendors")
      self.drop_down_vendor_id.items = [
        (vendor.get("company_name", vendor["_id"]), vendor["_id"])
        for vendor in vendor_list
      ]
    except Exception as e:
      Notification(f"⚠️ Could not load vendor list: {e}", style="warning").show()
      self.drop_down_vendor_id.items = []

    self.vendor_data = vendor_data or {
      "vendor_id": "",
      "vendor_part_no": "",
      "vendor_currency": "NZD",
      "vendor_price": 0.0,
      "cost_$NZ": 0.0,
      "cost_date": datetime.today().isoformat()
    }

    is_active = self.vendor_data.get("vendor_id") == self.part.get("default_vendor", "")
    self.button_delete_vendor.visible = not is_active

    self.drop_down_vendor_currency.items = ["NZD", "USD", "AU", "EUR", "STG", "SGD"]

    self.label_id.text = part.get("_id", "")
    self.label_id.role = "label-border"
    self.drop_down_vendor_id.selected_value = self.vendor_data["vendor_id"]
    self.text_box_vendor_part_no.text = self.vendor_data["vendor_part_no"]
    self.drop_down_vendor_currency.selected_value = self.vendor_data["vendor_currency"]
    self.text_box_vendor_price.text = str(self.vendor_data["vendor_price"])

    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"
    self.update_cost_nz()

  def get_exchange_rate(self, currency):
    rates = {"NZD": 1.0, "USD": 1.65, "AU": 1.08, "EUR": 1.94, "STG": 2.25, "SGD": 1.29}
    return rates.get(currency, 1.0)

  def update_cost_nz(self):
    try:
      price = float(self.text_box_vendor_price.text)
      rate = self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)
      cost_nz = round(price * rate, 2)
      timestamp = datetime.now().isoformat()

      self.vendor_data["cost_$NZ"] = cost_nz
      self.vendor_data["cost_date"] = timestamp

      self.label_cost_nz.text = f"≈ ${cost_nz:.2f} NZD"
      self.label_date_costed.text = timestamp[:10]  # strip time
    except:
      self.label_cost_nz.text = "Invalid price"
      self.label_date_costed.text = ""

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
      "cost_date": self.vendor_data["cost_date"]  # keep full timestamp
    })

    if self.part.get("default_vendor") != self.vendor_data["vendor_id"]:
      self.part["default_vendor"] = self.vendor_data["vendor_id"]

    # Insert or update vendor entry
    updated = False
    for idx, vendor in enumerate(self.part["vendor_part_numbers"]):
      if vendor["vendor_id"] == self.vendor_data["vendor_id"]:
        self.part["vendor_part_numbers"][idx] = self.vendor_data
        updated = True
        break

    if not updated:
      self.part["vendor_part_numbers"].append(self.vendor_data)

    # ✅ Update part.latest_cost
    self.part["latest_cost"] = {
      "cost_nz": self.vendor_data["cost_$NZ"],
      "cost_date": self.vendor_data["cost_date"]
    }

    try:
      validated = anvil.server.call("save_part_from_client", self.part)
      Notification("✅ Vendor details and cost saved.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to save vendor: {e}", style="danger").show()

    open_form("PartVendorRecords",
              part=self.part,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)

  def button_cancel_click(self, **event_args):
    open_form("PartVendorRecords",
              part=self.part,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)

  def button_delete_vendor_click(self, **event_args):
    vendor_id = self.vendor_data.get("vendor_id", "")
    if not vendor_id:
      Notification("⚠️ No vendor selected for deletion.", style="warning").show()
      return

    confirm_delete = confirm(f"Are you sure you want to delete vendor '{vendor_id}' from this part?")
    if not confirm_delete:
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

    open_form("PartVendorRecords",
              part=self.part,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)




