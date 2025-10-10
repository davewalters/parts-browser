from anvil import *
import anvil.server

from ._anvil_designer import CellRecordsTemplate

class CellRecords(CellRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Roles
    self.button_home.role = "mydefault-button"
    self.button_new_cell.role = "new-button"
    self.repeating_panel_cells.role = "scrolling-panel"

    # Wire RP events
    self.repeating_panel_cells.item_template = "CellRecords.CellRecordsRow"
    self.repeating_panel_cells.set_event_handler("x-show-detail", self._show_detail)
    self.repeating_panel_cells.set_event_handler("x-show-operator", self._show_operator)

    # Load
    self._load_cells()

  def form_show(self, **event_args):
    self._load_cells()

  # -----------------------------
  # Data load
  # -----------------------------
  def _load_cells(self):
    try:
      rows = anvil.server.call("cells_list", True)  # active_only=True
      self.repeating_panel_cells.items = rows
      self.label_summary.text = f"{len(rows)} active cells"
    except Exception as e:
      self.repeating_panel_cells.items = []
      self.label_summary.text = f"Load failed: {e}"

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
    Pre-create a minimal cell (no default bin required), then open editor.
    """
    try:
      new_id = anvil.server.call("generate_next_cell_id")
      skeleton = {
        "_id": new_id,
        "name": "",
        "type": "work_center",
        "active": True,
        "parallel_capacity": 1,
        "minute_cost_nz": 0.00,
        "default_wip_bin_id": None,   # allow None at create-time
      }
      # Create on server so auto-saves in the editor have a real record
      anvil.server.call("cells_create", skeleton)
  
      # Open the record editor; when the user navigates back, we’ll reload the list
      open_form("CellRecord", cell_id=new_id, is_new=False)
  
    except Exception as e:
      Notification(f"Could not create new cell: {e}", style="danger").show()


