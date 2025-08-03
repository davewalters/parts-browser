from ._anvil_designer import InventoryTransfersTemplate
from anvil import *
import anvil.server
from datetime import datetime

class InventoryTransfers(InventoryTransfersTemplate):
  def __init__(self, inventory_part_id=None,
               prev_filter_part_id="",
               prev_filter_part_name="",
               prev_filter_kanban="",
               **kwargs):
    self.init_components(**kwargs)
    self.part_id = inventory_part_id
    self.prev_filter_part_id = prev_filter_part_id
    self.prev_filter_part_name = prev_filter_part_name
    self.prev_filter_kanban = prev_filter_kanban
    self.status_fields = [
      "qty_on_order", "qty_on_hand", "qty_committed", "qty_picked", "qty_issued"
    ]
  
    self.drop_down_source.items = self.status_fields
    self.drop_down_target.items = self.status_fields
  
    self.load_part()
  
  def load_part(self):
    row = anvil.server.call("get_inventory_status_by_part", self.part_id)
    self.row = row
    self.label_part_id.text = row["part_id"]
    self.label_part_name.text = row.get("part_name", "<unknown>")
    for field in self.status_fields:
      getattr(self, f"label_{field}").text = str(row.get(field, 0))
  
  def button_transfer_click(self, **event_args):
    source = self.drop_down_source.selected_value
    target = self.drop_down_target.selected_value
    try:
      qty = float(self.text_box_qty.text)
      result = anvil.server.call("transfer_inventory_status", self.part_id, source, target, qty)
      Notification(f"Transferred {qty} from {source} to {target}", style="success").show()
      self.load_part()
    except Exception as e:
      alert(f"Transfer failed: {e}")

  def button_back_click(self, **event_args):
    open_form("InventoryRecords",
              filter_part_id = self.prev_filter_part_id,
              filter_part_name = self.prev_filter_part_name,
              filter_kanban = self.prev_filter_kanban
             )


