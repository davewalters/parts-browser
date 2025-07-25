from ._anvil_designer import PurchaseOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class PurchaseOrderRecord(PurchaseOrderRecordTemplate):
  def __init__(self, purchase_order_id=None, **properties):
    self.init_components(**properties)
    self.button_back.role = "mydefault-button"
    self.button_add_item.role = "new-button"
    self.drop_down_status.items = ["open", "partial", "closed", "cancelled"]
    self.drop_down_payment_method.items = ["Visa", "PayPal", "Eftpos", "Account"]

    self.purchase_order = {}
    self.vendors = []
    self.is_new = purchase_order_id is None

    self.load_vendor_dropdown()

    if not self.is_new:
      try:
        fetched = anvil.server.call("get_purchase_order", purchase_order_id)
        if fetched is None:
          Notification(f"⚠️ Purchase Order ID '{purchase_order_id}' not found in database.", style="warning").show()
        else:
          self.purchase_order = fetched
      except Exception as e:
        Notification(f"❌ Failed to load purchase order: {e}", style="danger").show()
    else:
      self.purchase_order = {
        "_id": anvil.server.call("generate_purchase_order_id"),
        "status": "open",
        "order_date": datetime.now().date().isoformat(),
        "due_date": datetime.now().date().isoformat(),
        "payment_method": "Visa",
        "paid": False,
        "order_cost_nz": 0.0,
        "lines": []
      }

    self.populate_form()
    self.repeating_panel_lines.set_event_handler("x-refresh-line-cost", self.refresh_line_cost)
    self.repeating_panel_lines.set_event_handler("x-delete-po-line", self.delete_line_item)


  def populate_form(self):
    self.label_id.text = self.purchase_order.get("_id", "")
    self.drop_down_status.selected_value = self.purchase_order.get("status", "open")
    self.date_picker_date_ordered.date = self.parse_date(self.purchase_order.get("order_date"))
    self.date_picker_date_due.date = self.parse_date(self.purchase_order.get("due_date"))
    self.drop_down_payment_method.selected_value = self.purchase_order.get("payment_method", "Visa")
    self.check_box_paid.checked = self.purchase_order.get("paid", False)
    self.label_order_cost_nz.text = self.format_currency(self.purchase_order.get("order_cost_nz", 0.0))
    self.text_area_notes.text = self.purchase_order.get("notes", "")

    vendor_id = self.purchase_order.get("vendor_id")
    if vendor_id:
      self.drop_down_vendor_name.selected_value = vendor_id

    for line in self.purchase_order["lines"]:
      line["purchase_order_id"] = self.purchase_order["_id"]
    self.repeating_panel_lines.items = self.purchase_order["lines"]

  def load_vendor_dropdown(self):
    self.vendors = anvil.server.call("get_filtered_vendors")
    self.drop_down_vendor_name.items = [(v["company_name"], v["_id"]) for v in self.vendors]

  def get_selected_vendor_name(self):
    vendor_id = self.drop_down_vendor_name.selected_value
    return next((v["company_name"] for v in self.vendors if v["_id"] == vendor_id), "")

  def format_date(self, date_input):
    if isinstance(date_input, datetime):
      return date_input.date().isoformat()
    elif isinstance(date_input, date):
      return date_input.isoformat()
    elif isinstance(date_input, str):
      return date_input.split("T")[0] if "T" in date_input else date_input
    return "1970-01-01"

  def parse_date(self, date_input):
    if isinstance(date_input, str):
      return datetime.fromisoformat(date_input).date()
    elif isinstance(date_input, datetime):
      return date_input.date()
    elif isinstance(date_input, date):
      return date_input
    return datetime(1970, 1, 1).date()

  def format_currency(self, value):
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"

  def button_back_click(self, **event_args):
    open_form("PurchaseOrderRecords")

  def button_add_item_click(self, **event_args):
    new_line = {
      "part_id": "",
      "vendor_part_no": "",
      "description": "",
      "qty_ordered": 0.0,
      "qty_received": 0.0,
      "vendor_unit_cost": 0.0,
      "vendor_currency": "NZD",
      "total_cost_nz": 0.0,
      "delivery_date": date.today().isoformat(),
      "purchase_order_id": self.label_id.text
    }
    self.repeating_panel_lines.items = self.repeating_panel_lines.items + [new_line]

  def refresh_line_cost(self, row_index, part_id, qty_ordered, **event_args):
    try:
      part = anvil.server.call("get_part", part_id) if part_id else {}
      cost_nz = float(part.get("latest_cost", {}).get("cost_nz", 0.0))
      line_total = qty_ordered * cost_nz

      default_vendor = part.get("default_vendor")
      po_vendor = self.drop_down_vendor_name.selected_value
      if default_vendor != po_vendor:
        Notification(f"⚠️ Default vendor for part '{part_id}' is missing or does not match the purchase order vendor.", style="warning").show()

      vendor_price = 0.0
      vendor_currency = "NZD"
      for v in part.get("vendor_part_numbers", []):
        if v.get("vendor_id") == default_vendor:
          vendor_price = float(v.get("vendor_price", 0.0))
          vendor_currency = v.get("vendor_currency", "NZD")
          break

      self.repeating_panel_lines.items[row_index]["vendor_unit_cost"] = vendor_price
      self.repeating_panel_lines.items[row_index]["vendor_currency"] = vendor_currency
      self.repeating_panel_lines.items[row_index]["total_cost_nz"] = round(line_total, 2)
      self.repeating_panel_lines.items = self.repeating_panel_lines.items  # Trigger UI refresh

    except Exception as e:
      Notification(f"⚠️ Failed to refresh cost: {e}", style="warning").show()

  def button_save_click(self, **event_args):
    try:
      lines = self.repeating_panel_lines.items
      if not lines:
        raise ValueError("At least one line item is required.")

      total_cost_nz = 0.0
      for line in lines:
        qty = float(line.get("qty_ordered", 0))
        part_id = line.get("part_id", "")
        part = anvil.server.call("get_part", part_id) if part_id else {}
        cost_nz = float(part.get("latest_cost", {}).get("cost_nz", 0.0))
        line_total = qty * cost_nz

        default_vendor = part.get("default_vendor")
        po_vendor = self.drop_down_vendor_name.selected_value
        if default_vendor != po_vendor:
          Notification(f"⚠️ Default vendor for part '{part_id}' is missing or does not match the purchase order vendor.", style="warning").show()
          open_form("PartVendorRecords", part_id=part_id, back_to_po=True, purchase_order_id=self.label_id.text)
          return

        vendor_price = 0.0
        vendor_currency = "NZD"
        for v in part.get("vendor_part_numbers", []):
          if v.get("vendor_id") == default_vendor:
            vendor_price = float(v.get("vendor_price", 0.0))
            vendor_currency = v.get("vendor_currency", "NZD")
            break

        line["vendor_unit_cost"] = vendor_price
        line["vendor_currency"] = vendor_currency
        line["total_cost_nz"] = round(line_total, 2)
        total_cost_nz += line_total

      purchase_order = {
        "_id": self.label_id.text.strip(),
        "status": self.drop_down_status.selected_value,
        "order_date": self.format_date(self.date_picker_date_ordered.date),
        "due_date": self.format_date(self.date_picker_date_due.date),
        "payment_method": self.drop_down_payment_method.selected_value,
        "paid": self.check_box_paid.checked,
        "vendor_id": self.drop_down_vendor_name.selected_value,
        "vendor_name": self.get_selected_vendor_name(),
        "order_cost_nz": round(total_cost_nz, 2),
        "lines": lines,
        "notes": self.text_area_notes.text
      }

      anvil.server.call("save_purchase_order", purchase_order)
      Notification("✅ Purchase order saved.", style="success").show()
      open_form("PurchaseOrderRecords")

    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  def delete_line_item(self, row_index, **event_args):
    items = list(self.repeating_panel_lines.items)
    del items[row_index]
    self.repeating_panel_lines.items = items








