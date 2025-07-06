# VendorDetails Form - Create or edit a single vendor entry

from anvil import *
from ._anvil_designer import VendorDetailsTemplate
import anvil.http
import json
from datetime import datetime

class VendorDetails(VendorDetailsTemplate):
  def __init__(self, part, vendor_data=None, **kwargs):
    self.init_components(**kwargs)
    self.part = part
    self.vendor_data = vendor_data or {
      "vendor_id": "",
      "vendor_part_no": "",
      "vendor_currency": "NZD",
      "vendor_price": 0.0,
      "cost_$NZ": 0.0,
      "cost_date": datetime.today().date().isoformat()
    }

    # Set dropdown choices here
    self.drop_down_vendor_currency.items = ["NZD", "USD", "AU", "EUR", "STG", "SGD"]

    # Populate fields
    self.label_id.text = part.get("_id", "")
    self.text_box_vendor_id.text = self.vendor_data["vendor_id"]
    self.text_box_vendor_part_no.text = self.vendor_data["vendor_part_no"]
    self.drop_down_vendor_currency.selected_value = self.vendor_data["vendor_currency"]
    self.text_box_vendor_price.text = str(self.vendor_data["vendor_price"])
    self.text_box_cost_date.text = self.vendor_data["cost_date"]
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_currency.selected_value)}"

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
      self.vendor_data["cost_$NZ"] = cost_nz
      self.label_cost_nz.text = f"≈ ${cost_nz:.2f} NZD"
    except:
      self.label_cost_nz.text = "Invalid price"

  def drop_down_currency_change(self, **event_args):
    self.label_exchange_rate.text = f"Rate: {self.get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"
    self.update_cost_nz()

  def text_box_price_change(self, **event_args):
    self.update_cost_nz()

  def button_save_click(self, **event_args):
    self.vendor_data.update({
      "vendor_id": self.text_box_vendor_id.text,
      "vendor_part_no": self.text_box_vendor_part_no.text,
      "vendor_currency": self.drop_down_vendor_currency.selected_value,
      "vendor_price": float(self.text_box_vendor_price.text),
      "cost_date": self.text_box_cost_date.text
    })
    self.vendor_data["cost_$NZ"] = round(self.vendor_data["vendor_price"] * self.get_exchange_rate(self.vendor_data["vendor_currency"]), 2)

    self.part.setdefault("vendor_part_numbers", []).append(self.vendor_data)
    anvil.http.request(
      url=f"http://127.0.0.1:8000/parts/{self.part['_id']}",
      method="PUT",
      data=json.dumps(self.part),
      headers={"Content-Type": "application/json"}
    )
    Notification("✅ Vendor saved.", style="success").show()
    open_form("VendorList", part=self.part)

  def button_cancel_click(self, **event_args):
    open_form("VendorList", part=self.part)

