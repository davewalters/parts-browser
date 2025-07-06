# VendorDetails Form - Create or edit a single vendor entry

from anvil import *
from ._anvil_designer import VendorDetailsTemplate
import anvil.http
import json
from datetime import datetime
from .. import VendorList

class VendorDetails(VendorDetailsTemplate):
  def __init__(self, part, vendor_data=None, filter_part="", filter_desc="", **kwargs):
    self.init_components(**kwargs)
    self.text_box_vendor_price.set_event_handler("change", self.text_box_vendor_price_change)
    self.drop_down_vendor_currency.set_event_handler("change", self.drop_down_currency_change)
    self.part = part
    self.prev_filter_part = filter_part
    self.prev_filter_desc = filter_desc
    try:
      vendor_response = anvil.http.request(
      url="http://127.0.0.1:8000/vendors",
      method="GET",
      json=True
      )
      # Each dropdown item is a (label, value) tuple
      self.drop_down_vendor_id.items = [
        (vendor.get("company_name", vendor["_id"]), vendor["_id"])
        for vendor in vendor_response
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
      "cost_date": datetime.today().date().isoformat()
    }

    self.drop_down_vendor_currency.items = ["NZD", "USD", "AU", "EUR", "STG", "SGD"]

    self.label_id.text = part.get("_id", "")
    self.label_id.role = "filter-border"
    self.drop_down_vendor_id.selected_value = self.vendor_data["vendor_id"]
    self.text_box_vendor_part_no.text = self.vendor_data["vendor_part_no"]
    self.drop_down_vendor_currency.selected_value = self.vendor_data["vendor_currency"]
    self.text_box_vendor_price.text = str(self.vendor_data["vendor_price"])
    self.text_box_cost_date.text = self.vendor_data["cost_date"]
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"

    self.update_cost_nz()

  def get_exchange_rate(self, currency):
    #2025-07-05
    rates = {"NZD": 1.0, "USD": 1.65, "AU": 1.08, "EUR": 1.94, "STG": 2.25, "SGD": 1.29}
    return rates.get(currency, 1.0)

  def update_cost_nz(self):
    try:
      price = float(self.text_box_vendor_price.text)
      rate = self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)
      cost_nz = round(price * rate, 2)
  
      # Update local vendor_data fields
      self.vendor_data["cost_$NZ"] = cost_nz
      self.vendor_data["cost_date"] = datetime.today().date().isoformat()
  
      self.label_cost_nz.text = f"≈ ${cost_nz:.2f} NZD"
      self.text_box_cost_date.text = self.vendor_data["cost_date"]
    except:
      self.label_cost_nz.text = "Invalid price"

  def drop_down_currency_change(self, **event_args):
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"
    self.update_cost_nz()

  def text_box_vendor_price_change(self, **event_args):
    self.update_cost_nz()

  def button_save_click(self, **event_args):
    # Save current form values into vendor_data
    self.vendor_data.update({
      "vendor_id": self.drop_down_vendor_id.selected_value,
      "vendor_part_no": self.text_box_vendor_part_no.text,
      "vendor_currency": self.drop_down_vendor_currency.selected_value,
      "vendor_price": float(self.text_box_vendor_price.text),
      "cost_date": self.text_box_cost_date.text
    })
    # Update default_vendor if this vendor is not already the default
    if self.part.get("default_vendor") != self.vendor_data["vendor_id"]:
      self.part["default_vendor"] = self.vendor_data["vendor_id"]
      
    # Recalculate NZ cost
    rate = self.get_exchange_rate(self.vendor_data["vendor_currency"])
    self.vendor_data["cost_$NZ"] = round(self.vendor_data["vendor_price"] * rate, 2)

    # Check if vendor exists (by vendor_id), update or append
    updated = False
    for idx, vendor in enumerate(self.part["vendor_part_numbers"]):
      if vendor["vendor_id"] == self.vendor_data["vendor_id"]:
        self.part["vendor_part_numbers"][idx] = self.vendor_data
        updated = True
        break
    if not updated:
      self.part["vendor_part_numbers"].append(self.vendor_data)
    
    self.part["default_vendor"] = self.vendor_data["vendor_id"]
    # Persist entire part document
    try:
      url = f"http://127.0.0.1:8000/parts/{self.part['_id']}"
      anvil.http.request(
        url=url,
        method="PUT",
        data=json.dumps(self.part),
        headers={"Content-Type": "application/json"}
      )
      Notification("✅ Vendor details saved.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to save vendor: {e}", style="danger").show()

    # Return to vendor list
    open_form("VendorList",
              part=self.part,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc)

  def button_cancel_click(self, **event_args):
    open_form("VendorList",
              part=self.part,
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc)


