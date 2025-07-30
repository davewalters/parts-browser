from ._anvil_designer import InventoryRecordTemplate
from anvil import *
import anvil.server
from datetime import datetime

class InventoryRecord(InventoryRecordTemplate):
  def __init__(self,
               inventory_part_id=None,
               prev_filter_part_id="",
               prev_filter_part_name="",
               prev_filter_kanban=None,
               **properties):
    self.init_components(**properties)

    # Store filter state
    self.prev_filter_part_id = prev_filter_part_id
    self.prev_filter_part_name = prev_filter_part_name
    self.prev_filter_kanban = prev_filter_kanban

    # Load inventory for the part
    self.part_id = inventory_part_id
    self.rows = anvil.server.call('get_inventory_by_part', self.part_id)

    # Extract part name from first row (joined part)
    part_info = self.rows[0]["part"] if self.rows else {}
    self.label_part_id.text = part_info.get("_id", "")
    self.label_part_name.text = part_info.get("name", "")

    # Set kanban status (global per part)
    self.check_box_kanban.checked = all(r.get("is_kanban", False) for r in self.rows)

    # Unique bin names for dropdowns
    self.bins = sorted(list(set(r["bin"] for r in self.rows)))
    self.drop_down_source_bin.items = self.bins
    self.drop_down_target_bin.items = self.bins + ["<new>"]

    # Load rows into panel
    self.repeating_panel_bins.items = self.rows

  def back_button_click(self, **event_args):
    open_form("InventoryRecords",
              filter_part_id=self.prev_filter_part_id,
              filter_part_name=self.prev_filter_part_name,
              filter_kanban=self.prev_filter_kanban)

  def check_box_kanban_change(self, **event_args):
    new_kanban = self.check_box_kanban.checked
    for r in self.rows:
      r["is_kanban"] = new_kanban
    Notification(f"Kanban status set to {'enabled' if new_kanban else 'disabled'}", style="success").show()

  def get_transfer_params(self):
    try:
      qty = float(self.text_box_transfer_qty.text)
      if qty <= 0:
        raise ValueError("Quantity must be positive.")
      return {
        "source_bin": self.drop_down_source_bin.selected_value,
        "target_bin": self.drop_down_target_bin.selected_value,
        "qty": qty
      }
    except Exception as e:
      alert(f"Invalid transfer parameters: {e}")
      return None

  def button_save_click(self, **event_args):
    saved = 0
    failed = 0
  
    for row in self.rows:
      try:
        # Optionally validate here
        for field in ["qty_on_hand", "qty_committed", "qty_staged", "qty_issued", "qty_on_order"]:
          if row.get(field, 0) < 0:
            raise ValueError(f"{field} cannot be negative in bin '{row['bin']}'")
  
        row["last_updated"] = datetime.utcnow()
        anvil.server.call('save_inventory_row', row)
        saved += 1
      except Exception as e:
        print(f"❌ Save failed for bin '{row.get('bin')}', reason: {e}")
        failed += 1
  
    if saved:
      Notification(f"✅ {saved} rows saved.", style="success").show()
    if failed:
      Notification(f"⚠️ {failed} rows failed to save.", style="warning").show()


