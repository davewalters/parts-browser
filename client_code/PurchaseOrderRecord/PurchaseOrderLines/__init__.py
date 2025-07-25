from ._anvil_designer import PurchaseOrderLinesTemplate
from anvil import *

class PurchaseOrderLines(PurchaseOrderLinesTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.update_ui_from_item()

  def update_ui_from_item(self):
    self.text_box_part_id.text = self.item.get("part_id", "")
    self.text_box_qty_ordered.text = str(self.item.get("qty_ordered", ""))
    self.text_box_qty_received.text = str(self.item.get("qty_received", ""))
    self.label_vendor_part_no.text = self.item.get("vendor_part_no", "")
    self.label_description.text = self.item.get("description", "")
    self.label_vendor_currency.text = self.item.get("vendor_currency", "NZD")
    self.label_vendor_unit_price.text = self.format_currency(self.item.get("vendor_unit_cost", 0))
    self.label_total_cost_nz.text = self.format_currency(self.item.get("total_cost_nz", 0))

  def get_repeating_panel(self):
    parent = self.parent
    while parent:
      if hasattr(parent, "items"):
        return parent
      parent = parent.parent
    return None

  def try_refresh_line(self):
    try:
      part_id = self.text_box_part_id.text.strip()
      qty = float(self.text_box_qty_ordered.text or "0")
      self.item["part_id"] = part_id
      self.item["qty_ordered"] = qty

      if not part_id or qty <= 0:
        return

      panel = self.get_repeating_panel()
      if panel and self.item in panel.items:
        row_index = panel.items.index(self.item)
        panel.raise_event("x-refresh-line-cost", row_index=row_index, part_id=part_id, qty_ordered=qty)
    except ValueError:
      Notification("⚠️ Invalid quantity format", style="warning").show()

  def text_box_part_id_lost_focus(self, **event_args):
    self.try_refresh_line()

  def text_box_qty_ordered_lost_focus(self, **event_args):
    self.try_refresh_line()

  def text_box_qty_ordered_pressed_enter(self, **event_args):
    self.try_refresh_line()

  def text_box_qty_received_lost_focus(self, **event_args):
    try:
      self.item["qty_received"] = float(self.text_box_qty_received.text or "0")
    except ValueError:
      Notification("⚠️ Invalid received quantity", style="warning").show()

  def button_edit_price_click(self, **event_args):
    if not self.item.get("part_id"):
      Notification("⚠️ Enter a Part ID first", style="warning").show()
      return
    panel = self.get_repeating_panel()
    if panel:
      panel.raise_event("x-save-purchase-order")
    open_form("PartVendorRecord", 
              part_id=self.item["part_id"], 
              back_to_po=True, 
              purchase_order_id=self.item.get("purchase_order_id", ""))

  def button_view_click(self, **event_args):
    if not self.item.get("part_id"):
      Notification("⚠️ Enter a Part ID first", style="warning").show()
      return
    panel = self.get_repeating_panel()
    if panel:
      panel.raise_event("x-save-purchase-order")
    open_form("PartVendorRecords", 
              part_id=self.item["part_id"], 
              back_to_po=True, 
              purchase_order_id=self.item.get("purchase_order_id", ""))

  def button_delete_click(self, **event_args):
    if confirm("Delete this line item?"):
      panel = self.get_repeating_panel()
      if panel:
        row_index = panel.items.index(self.item)
        panel.raise_event("x-delete-po-line", row_index=row_index)

  def refresh_data_bindings(self):
    self.update_ui_from_item()

  def format_currency(self, value):
    try:
      return f"{float(value):.2f}"
    except (ValueError, TypeError):
      return "–"









  

  







