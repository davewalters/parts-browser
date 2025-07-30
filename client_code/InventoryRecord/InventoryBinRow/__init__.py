from ._anvil_designer import InventoryBinRowTemplate
from anvil import *
from datetime import datetime

class InventoryBinRow(InventoryBinRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_transfer.set_event_handler("click", self.transfer_stock)

  def transfer_stock(self, **event_args):
    parent_form = self.parent.parent  # InventoryRecord
    params = parent_form.get_transfer_params()
    if not params:
      return

    source_bin = params["source_bin"]
    target_bin = params["target_bin"]
    qty = params["qty"]

    row = self.item
    if row["bin"] != source_bin:
      alert(f"Cannot transfer from this row: it is not the selected source bin.")
      return

    if row.get("is_kanban", False):
      alert("Cannot transfer from a Kanban bin.")
      return

    if qty > row["qty_on_hand"]:
      alert(f"Not enough stock. Available: {row['qty_on_hand']}")
      return

    # Locate or create target row
    target_row = next((r for r in parent_form.rows if r["bin"] == target_bin), None)
    if not target_row:
      target_row = {
        "part_id": parent_form.part_id,
        "bin": target_bin,
        "owner": "Manufacturing",
        "is_kanban": False,
        "qty_on_hand": 0,
        "qty_committed": 0,
        "qty_staged": 0,
        "qty_issued": 0,
        "qty_on_order": 0,
        "last_updated": datetime.utcnow(),
        "notes": ""
      }
      parent_form.rows.append(target_row)
      parent_form.bins.append(target_bin)
      parent_form.drop_down_source_bin.items = parent_form.bins
      parent_form.drop_down_target_bin.items = parent_form.bins + ["<new>"]

    # Perform transfer
    row["qty_on_hand"] -= qty
    target_row["qty_on_hand"] += qty
    row["last_updated"] = target_row["last_updated"] = datetime.utcnow()

    parent_form.repeating_panel_bins.items = parent_form.rows
    Notification(f"Transferred {qty} from {source_bin} to {target_bin}", style="success").show()

