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
    Generate a new id, pre-create the record (server upsert), then open editor.
    """
    try:
      new_id = anvil.server.call("generate_next_cell_id")
      # Pre-create so on-change saves have a target
      skeleton = {
        "_id": new_id,
        "name": "",
        "type": "work_center",
        "active": True,
        "parallel_capacity": 1,
        "minute_cost_nz": 0.00,
        "default_wip_bin_id": "",
      }
      try:
        anvil.server.call("cells_upsert", skeleton)
      except Exception:
        pass
      open_form("CellRecord", cell_id=new_id)
    except Exception as e:
      Notification(f"Could not create new cell id: {e}", style="danger").show()

