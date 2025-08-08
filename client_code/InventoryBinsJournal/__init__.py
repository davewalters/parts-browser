# client code: InventoryBinsJournal
from ._anvil_designer import InventoryBinsJournalTemplate
from anvil import *
import anvil.server

class InventoryBinsJournal(InventoryBinsJournalTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Update on change for consistency with other forms
    self.text_box_part_id.set_event_handler("pressed_enter", self.update_filter)
    self.text_box_part_name.set_event_handler("pressed_enter", self.update_filter)
    self.check_box_kanban.set_event_handler("change", self.update_filter)

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

      # Pre-format for the row template
      for e in entries:
        ts = e.get("timestamp")
        e["formatted_timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
        # Ensure numeric columns exist
        e["qty"] = e.get("qty", 0) or 0
        e["running_balance_source"] = e.get("running_balance_source", None)
        e["running_balance_target"] = e.get("running_balance_target", None)
        e["source_bin_id"] = e.get("source_bin_id", "")
        e["target_bin_id"] = e.get("target_bin_id", "")

      self.repeating_panel_entries.items = entries
      self.label_row_count.text = f"{len(entries)} row(s)"
    except Exception as err:
      self.repeating_panel_entries.items = []
      self.label_row_count.text = f"Error: {err}"

  def button_home_click(self, **event_args):
    open_form("Nav")


