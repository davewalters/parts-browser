from anvil import *
import anvil.server

from ._anvil_designer import CellRecordTemplate

CELL_TYPES = [
  # keep aligned with model's Literal for now
  "work_center", "assembly", "inspection", "test", "inwards_goods", "dispatch", "other"
]
# Alt terms to consider later:
#   receiving, putaway, kitting, staging, picking, packing, shipping, dispatch, fg_putaway

class CellRecord(CellRecordTemplate):
  def __init__(self, cell_id: str, is_new: bool=False, **kwargs):
    self.init_components(**kwargs)

    # Roles
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"

    # State
    self._cell = {}
    self._cell_id = cell_id
    self._is_new = bool(is_new)

    # Dropdown items
    self.drop_down_cell_type.items = CELL_TYPES

    # Ensure we have an id
    if not self._cell_id:
      try:
        self._cell_id = anvil.server.call("generate_next_cell_id")
        self._is_new = True
      except Exception as e:
        Notification(f"Could not generate cell id: {e}", style="danger").show()
        self._cell_id = "CELL-NEW"

    # For "update on change", ensure a record exists
    if self._is_new:
      skeleton = {
        "_id": self._cell_id,
        "name": "",
        "type": "work_center",
        "active": True,
        "parallel_capacity": 1,
        "minute_cost_nz": 0.00,
        "default_wip_bin_id": "",
      }
      try:
        self._cell = anvil.server.call("cells_upsert", skeleton) or skeleton
        self._is_new = False
      except Exception:
        self._cell = skeleton

    # Load latest & bind
    self._load_cell()
    self._bind_fields()

    # Auto-save events (update on change)
    self.text_name.set_event_handler("lost_focus", self._save_from_ui)
    self.drop_down_cell_type.set_event_handler("change", self._save_from_ui)
    self.check_box_active.set_event_handler("change", self._save_from_ui)
    self.text_parallel_capacity.set_event_handler("lost_focus", self._save_from_ui)
    self.text_minute_cost_nz.set_event_handler("lost_focus", self._save_from_ui)
    self.text_default_wip_bin_id.set_event_handler("lost_focus", self._save_from_ui)

  # -----------------------------
  # Load & bind
  # -----------------------------
  def _load_cell(self):
    try:
      fetched = anvil.server.call("cells_get", self._cell_id)
      if fetched:
        self._cell = fetched
      else:
        self._cell["_id"] = self._cell_id
    except Exception as e:
      Notification(f"Failed to load cell: {e}", style="danger").show()

  def _bind_fields(self):
    c = self._cell or {}
    # ID as label (read-only)
    self.label_cell_id.text = c.get("_id", "")

    # Editable fields
    self.text_name.text = c.get("name", "")
    ctype = c.get("type", "work_center")
    self.drop_down_cell_type.selected_value = ctype if ctype in self.drop_down_cell_type.items else "work_center"
    self.check_box_active.checked = bool(c.get("active", True))
    self.text_parallel_capacity.text = str(int(c.get("parallel_capacity", 1)))
    try:
      self.text_minute_cost_nz.text = f"{float(c.get('minute_cost_nz', 0.0)):.2f}"
    except Exception:
      self.text_minute_cost_nz.text = "0.00"
    self.text_default_wip_bin_id.text = c.get("default_wip_bin_id", "")

  # -----------------------------
  # Auto-save (update on change)
  # -----------------------------
  def _save_from_ui(self, **event_args):
    try:
      updated = dict(self._cell)
      updated["_id"] = self.label_cell_id.text.strip()
      updated["name"] = (self.text_name.text or "").strip()
      updated["type"] = self.drop_down_cell_type.selected_value or "work_center"
      updated["active"] = bool(self.check_box_active.checked)

      # Capacity (int >=1)
      try:
        cap = int((self.text_parallel_capacity.text or "1").strip())
        updated["parallel_capacity"] = max(1, cap)
      except Exception:
        updated["parallel_capacity"] = 1
        self.text_parallel_capacity.text = "1"

      # Minute cost (float >=0)
      try:
        cost = float((self.text_minute_cost_nz.text or "0").replace("$","").replace(",","").strip())
        updated["minute_cost_nz"] = max(0.0, cost)
        self.text_minute_cost_nz.text = f"{updated['minute_cost_nz']:.2f}"
      except Exception:
        updated["minute_cost_nz"] = 0.0
        self.text_minute_cost_nz.text = "0.00"

      updated["default_wip_bin_id"] = (self.text_default_wip_bin_id.text or "").strip()

      saved = anvil.server.call("cells_upsert", updated) or updated
      self._cell = saved

    except Exception as e:
      Notification(f"Save failed: {e}", style="danger").show()

  # -----------------------------
  # Navigation / delete
  # -----------------------------
  def button_back_click(self, **event_args):
    open_form("CellRecords")

  def button_delete_click(self, **event_args):
    cid = (self.label_cell_id.text or "").strip()
    if not cid:
      Notification("No cell id.", style="warning").show()
      return
    if confirm(f"Are you sure you want to delete cell '{cid}'?"):
      try:
        anvil.server.call("cells_delete", cid)
        Notification("🗑️ Cell deleted.", style="danger").show()
        open_form("CellRecords")
      except Exception as e:
        Notification(f"Delete failed: {e}", style="danger").show()

