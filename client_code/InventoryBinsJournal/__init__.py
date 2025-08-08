from ._anvil_designer import InventoryBinsJournalTemplate
from anvil import *
import anvil.server
from datetime import datetime

class InventoryBinsJournal(InventoryBinsJournalTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    self.text_box_part_id.set_event_handler("pressed_enter", self.update_filter)
    self.text_box_part_name.set_event_handler("pressed_enter", self.update_filter)
    self.check_box_kanban.set_event_handler("change", self.update_filter)

    # First load: don't fetch until there's a filter
    self.update_filter(initial=True)

  def update_filter(self, initial=False, **event_args):
    part_id = (self.text_box_part_id.text or "").strip()
    part_name = (self.text_box_part_name.text or "").strip()
    is_kanban = bool(self.check_box_kanban.checked)

    # Guard: avoid calling the server with empty filters on first load
    if initial and not part_id and not part_name:
      self.repeating_panel_entries.items = []
      self.label_row_count.text = "Enter a Part ID or Part Name to view bin journal."
      return

    try:
      if not part_id and not part_name:
        # If user clears filters, show empty state rather than error
        self.repeating_panel_entries.items = []
        self.label_row_count.text = "Enter a Part ID or Part Name to view bin journal."
        return

      entries = anvil.server.call(
        "get_inventory_bins_journal",
        part_id=part_id,
        part_name=part_name,
        is_kanban=is_kanban
      )

      # Defensive shaping for the row template
      shaped = []
      for e in entries:
        ts = e.get("timestamp")
        # timestamp might already be tz-adjusted datetime from server, but guard anyway
        if isinstance(ts, datetime):
          formatted_ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        else:
          formatted_ts = ""

        delta = e.get("delta", {}) or {}
        shaped.append({
          **e,
          "formatted_timestamp": formatted_ts,
          "formatted_balance": f"{float(e.get('running_balance', 0) or 0):.2f}",
          "qty": delta.get("qty", 0),
          # These make it easy to bind in the row without KeyErrors
          "bin_id": e.get("_id", ""),          # <- prevent KeyError if missing
          "source_bin_id": e.get("source_bin_id", ""),
          "target_bin_id": e.get("target_bin_id", ""),
        })

      self.repeating_panel_entries.items = shaped
      self.label_row_count.text = f"{len(shaped)} row(s)"

    except Exception as ex:
      self.repeating_panel_entries.items = []
      self.label_row_count.text = f"Error: {ex}"

  def button_home_click(self, **event_args):
    open_form("Nav")

