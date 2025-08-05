from ._anvil_designer import InventoryJournalViewerTemplate
from anvil import *
import anvil.server

class InventoryJournalViewer(InventoryJournalViewerTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    self.text_box_part_id.set_event_handler("lost_focus", self.update_filter)
    self.text_box_part_name.set_event_handler("lost_focus", self.update_filter)
    self.check_box_kanban.set_event_handler("change", self.update_filter)
    self.button_home.role = "mydefault-button"
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

    from ..InventoryJournalRow import InventoryJournalRow
    InventoryJournalRow.running_balance = None

    self.repeating_panel_entries.items = journal_entries
    self.label_row_count.text = f"{len(journal_entries)} row(s)"

  def button_home_click(self, **event_args):
    open_form("Nav")
