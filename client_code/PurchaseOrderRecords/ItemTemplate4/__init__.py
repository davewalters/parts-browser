from anvil import *
from ._anvil_designer import ItemTemplate4Template
from datetime import date, datetime

class ItemTemplate4(ItemTemplate4Template):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Set field values from item
    self.label_po.text = self.item.get("_id", "")
    self.label_vendor.text = self.item.get("vendor_name", "")

    order_date = self.item.get("order_date")
    self.label_order_date.text = self.format_date(order_date)

    self.label_status.text = self.item.get("status", "")

    due_date = self.item.get("due_date")
    self.label_due_date.text = self.format_date(due_date)

    cost = self.item.get("order_cost_nz", 0.0)
    self.label_total_cost_nz.text = f"${cost:,.2f}"

  def format_date(self, date_str):
    try:
      if isinstance(date_str, str):
        return date_str.split("T")[0]
      elif isinstance(date_str, (datetime, date)):
        return date_str.strftime("%Y-%m-%d")
    except:
      return "–"
    return "–"

  def button_show_details_click(self, **event_args):
    self.parent.raise_event("x-show-detail", po=self.item)

