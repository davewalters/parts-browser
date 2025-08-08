from ._anvil_designer import InventoryBinTransfersTemplate
from anvil import *
import anvil.server

class InventoryBinTransfers(InventoryBinTransfersTemplate):
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

    self.button_back.role = "mydefault-button"
    self.button_transfer.role = "save-button"

    if not self.part_id:
      alert("No part selected.")
      self.button_back_click()
      return

    self.load_part_and_bins()

  def load_part_and_bins(self):
    # (optional) fetch part name if you don't already have it
    try:
      part = anvil.server.call("get_part", self.part_id) or {}
    except Exception:
      part = {}
    self.label_part_id.text = self.part_id
    self.label_part_name.text = part.get("description", "<unknown>")

    try:
      bins = anvil.server.call("get_bins_by_part", self.part_id) or []
    except Exception as e:
      alert(f"Failed to load bins: {e}")
      bins = []

    # drop-down items: show "BINID — location — qty"
    def fmt(b):
      loc = b.get("location", "")
      qty = b.get("qty", 0)
      return f"{b['_id']} — {loc or '-'} — {qty}"

    self.drop_down_source_bin.items = [(fmt(b), b["_id"]) for b in bins]
    self.drop_down_target_bin.items = [(fmt(b), b["_id"]) for b in bins]

    self.repeating_panel_bins.items = bins

  def button_transfer_click(self, **event_args):
    src = self.drop_down_source_bin.selected_value
    tgt = self.drop_down_target_bin.selected_value
    try:
      qty = float(self.text_box_qty.text or "0")
    except ValueError:
      alert("Invalid qty")
      return

    if not src or not tgt:
      alert("Please select both Source and Target bins.")
      return

    try:
      anvil.server.call("transfer_inventory_bin", self.part_id, src, tgt, qty)
      Notification(f"Transferred {qty} from {src} to {tgt}", style="success").show()
      self.load_part_and_bins()
    except Exception as e:
      alert(f"Transfer failed: {e}")

  def button_back_click(self, **event_args):
    open_form("InventoryRecords",
              filter_part_id=self.prev_filter_part_id,
              filter_part_name=self.prev_filter_part_name,
              filter_kanban=self.prev_filter_kanban)

