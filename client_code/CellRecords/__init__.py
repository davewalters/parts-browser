from anvil import *
import anvil.server

from ._anvil_designer import CellRecordsTemplate

class CellRecords(CellRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Roles
    self.button_home.role = "mydefault-button"
    self.button_new_cell.role = "new-button"
    self.repeating_panel_1.role = "scrolling-panel"

    # Wire RP events
    self.repeating_panel_1.set_event_handler("x-show-detail", self._show_detail)
    self.repeating_panel_1.set_event_handler("x-show-operator", self._show_operator)

    # Load
    self._load_cells()

  # -----------------------------
  # Data load
  # -----------------------------
  def _load_cells(self):
    try:
      rows = anvil.server.call("cells_list") or []
      rows.sort(key=lambda r: ((r.get("name") or "").lower(), r.get("_id") or ""))
      self.repeating_panel_1.items = rows
      self.label_count.text = f"{len(rows)} cells"
    except Exception as e:
      #self.label_count.text = f"Error: {e}"
      self.repeating_panel_1.items = []

  # -----------------------------
  # Actions
  # -----------------------------
  def _show_detail(self, row, **event_args):
    try:
      open_form("CellRecord", cell_id=row.get("_id"))
    except Exception as e:
      alert(f"Error opening cell editor: {e}")

  def _show_operator(self, row, **event_args):
    try:
      open_form("CellDetail", cell_id=row.get("_id"))
    except Exception as e:
      alert(f"Error opening operator view: {e}")

  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_new_cell_click(self, **event_args):
    """
    Open editor in NEW mode (no pre-create). The editor will call cells_create() on first save.
    """
    try:
      # Let the record generate the id on first save
      open_form("CellRecord", cell_id="", is_new=True)
    except Exception as e:
      Notification(f"Could not open new cell editor: {e}", style="danger").show()

