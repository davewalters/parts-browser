from ._anvil_designer import InventoryStatusJournalTemplate
from anvil import *
import anvil.server

class InventoryStatusJournal(InventoryStatusJournalTemplate):
  def __init__(self, part_id: str | None = None, **properties):
    self.init_components(**properties)

    self.text_box_part_id.set_event_handler("pressed_enter", self.update_filter)
    self.text_box_part_name.set_event_handler("pressed_enter", self.update_filter)
    self.check_box_kanban.set_event_handler("change", self.update_filter)
    if part_id:
      self.text_box_part_id.text = part_id
    self.update_filter()

  def update_filter(self, **event_args):
    part_id = self.text_box_part_id.text.strip()
    part_name = self.text_box_part_name.text.strip()
    is_kanban = self.check_box_kanban.checked

    journal_entries = anvil.server.call(
      "get_inventory_journal",
      part_id=part_id,
      part_name=part_name,
      is_kanban=is_kanban
    )

    for entry in journal_entries:
      entry["formatted_timestamp"] = entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
      entry["formatted_balance"] = f"{entry.get('running_balance', 0):.2f}"

      delta = entry.get("delta", {})
      # Show zero rather than blank for all fields
      for field in ["qty_on_hand", "qty_committed", "qty_picked", "qty_issued", "qty_on_order"]:
        entry[field] = delta.get(field, 0)

    self.repeating_panel_entries.items = journal_entries
    self.label_row_count.text = f"{len(journal_entries)} row(s)"


  def button_home_click(self, **event_args):
    open_form("Nav")
