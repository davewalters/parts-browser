from ._anvil_designer import InventoryBinsJournalTemplate
from anvil import *
import anvil.server

class InventoryBinsJournal(InventoryBinsJournalTemplate):
  def __init__(self, part_id=None, **properties):
    self.init_components(**properties)

    self.text_box_part_id.set_event_handler("pressed_enter", self.update_filter)
    self.text_box_part_name.set_event_handler("pressed_enter", self.update_filter)
    self.check_box_kanban.set_event_handler("change", self.update_filter)

    if part_id:
      self.text_box_part_id.text = str(part_id)

    self.update_filter()

  def update_filter(self, **event_args):
    part_id = (self.text_box_part_id.text or "").strip()
    part_name = (self.text_box_part_name.text or "").strip()
    is_kanban = bool(self.check_box_kanban.checked)

    try:
      entries = anvil.server.call(
        "get_inventory_bins_journal",
        part_id=part_id,
        part_name=part_name,
        is_kanban=is_kanban
      )

      # Format for display
      for e in entries:
        ts = e.get("timestamp")
        try:
          e["formatted_timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
          e["formatted_timestamp"] = str(ts)

        # Always show zeros for empty deltas
        e["src_delta"] = float(e.get("src_delta") or 0.0)
        e["tgt_delta"] = float(e.get("tgt_delta") or 0.0)

        # Ensure strings for bins
        e["source_bin_id"] = e.get("source_bin_id") or ""
        e["target_bin_id"] = e.get("target_bin_id") or ""

      self.repeating_panel_entries.items = entries
      self.label_row_count.text = f"{len(entries)} row(s)"
    except Exception as ex:
      self.label_row_count.text = f"Error: {ex}"
      self.repeating_panel_entries.items = []

  def button_home_click(self, **event_args):
    open_form("Nav")



