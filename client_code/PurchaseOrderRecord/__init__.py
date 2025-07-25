from ._anvil_designer import PurchaseOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date, datetime


class PurchaseOrderRecord(PurchaseOrderRecordTemplate):
  def __init__(self, purchase_order_id, **properties):
    self.init_components(**properties)
    self.button_back.role = "mydefault-button"
    self.button_add_item.role = "new-button"
    self.drop_down_status.items = ["open", "partial", "closed", "cancelled"]
    self.drop_down_payment_method.items = ["Visa", "PayPal", "Eftpos", "Account"]

    self.purchase_order = {}
    self.is_new = purchase_order_id is None
    if not self.is_new:
      try:
        fetched = anvil.server.call("get_purchase_order", purchase_order_id)
        if fetched is None:
          Notification(f"⚠️ Purchase Order ID '{purchase_order_id}' not found in database.", style="warning").show()
        else:
          self.purchase_order = fetched
      except Exception as e:
        Notification(f"❌ Failed to load purchase order: {e}", style="danger").show()
    
    now = self.format_date(datetime.now().isoformat())
    self.label_id.text = self.purchase_order.get("_id", "")
    self.drop_down_status.selected_value = self.purchase_order.get("status", "open")
    self.date_picker_date_ordered.text = self.purchase_order.get("order_date", now)
    #vendor_name TODO
    self.date_picker_date_due.text = self.purchase_order.get("expected_date", now)
    self.drop_down_payment_method.selected_value = self.purchase_order.get("payment_method", "Visa")
    self.check_box_paid.checked = self.purchase_order.get("paid", False)
    self.text_box_order_cost_nz = self.purchase_order.get("order_cost_nz", 0.0)
    

    
  def get_vendor_id(self):
    try:
      vendor_list = anvil.server.call("get_all_vendors")
      self.drop_down_vendor_id.items = [
        (vendor.get("company_name", vendor["_id"]), vendor["_id"])
        for vendor in vendor_list
      ]
    except Exception as e:
      Notification(f"⚠️ Could not load vendor list: {e}", style="warning").show()
      self.drop_down_vendor_id.items = []

  def format_date(self, date_input):
    if isinstance(date_input, datetime):
      return date_input.date().isoformat()
    elif isinstance(date_input, date):
      return date_input.isoformat()
    elif isinstance(date_input, str):
      return date_input.split("T")[0] if "T" in date_input else date_input
    return "1970-01-01"
