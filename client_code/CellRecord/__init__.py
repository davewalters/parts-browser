from anvil import *
import anvil.server
from ._anvil_designer import CellRecordTemplate

CELL_TYPES = [
  "work_center", "assembly", "inspection", "test",
  "inwards_goods", "dispatch", "other"
]

class CellRecord(CellRecordTemplate):
  def __init__(self, cell_id: str = "", is_new: bool = False, **properties):
    self.init_components(**properties)

    # Roles
    self.button_back.role   = "mydefault-button"
    self.button_delete.role = "delete-button"

    # State
    self._cell_id = (cell_id or "").strip()
    self._is_new  = bool(is_new or not self._cell_id)
    self._cell    = {}

    # Dropdown items
    self.drop_down_cell_type.items = CELL_TYPES

    # If editing existing, fetch it; otherwise bind blanks
    if not self._is_new and self._cell_id:
      self._load_cell()
    else:
      # skeleton UI for a new record (no DB write yet)
      self._cell = {
        "_id": self._cell_id or "",
        "name": "",
        "type": "work_center",
        "active": True,
        "parallel_capacity": 1,
        "minute_cost_nz": 0.00,
        "default_wip_bin_id": None,
      }

    self._bind_fields()

    # Auto-save: update on change / lost_focus
    self.text_name.set_event_handler("lost_focus", self._save_from_ui)
    self.drop_down_cell_type.set_event_handler("change", self._save_from_ui)
    self.check_box_active.set_event_handler("change", self._save_from_ui)
    self.text_parallel_capacity.set_event_handler("lost_focus", self._save_from_ui)
    self.text_minute_cost_nz.set_event_handler("lost_focus", self._save_from_ui)
    self.text_default_wip_bin_id.set_event_handler("lost_focus", self._save_from_ui)

  # ---------- Load & bind ----------
  def _load_cell(self):
    try:
      doc = anvil.server.call("cells_get", self._cell_id)
      if not doc:
        Notification(f"Cell '{self._cell_id}' not found.", style="danger").show()
        self._is_new = True
        self._cell = {"_id": self._cell_id}
      else:
        self._cell = doc
    except Exception as e:
      Notification(f"Failed to load cell: {e}", style="danger").show()
      self._cell = {"_id": self._cell_id}

  def _bind_fields(self):
    c = self._cell or {}
    # ID
    self.label_cell_id.text = c.get("_id", "") or ("(new)" if self._is_new else "")

    # Editable fields
    self.text_name.text = c.get("name", "")
    ctype = c.get("type", "work_center")
    self.drop_down_cell_type.selected_value = (ctype if ctype in CELL_TYPES else "work_center")
    self.check_box_active.checked = bool(c.get("active", True))
    self.text_parallel_capacity.text = str(int(c.get("parallel_capacity", 1)))
    try:
      self.text_minute_cost_nz.text = f"{float(c.get('minute_cost_nz', 0.0)):.2f}"
    except Exception:
      self.text_minute_cost_nz.text = "0.00"
    self.text_default_wip_bin_id.text = (c.get("default_wip_bin_id") or "")  # allow None

    # Delete visible only for existing rows
    self.button_delete.visible = not self._is_new and bool(c.get("_id"))

  # ---------- Save (create on first, then update) ----------
  def _save_from_ui(self, **e):
    updated = {
      "_id": (self.label_cell_id.text or "").strip(),  # blank => new
      "name": (self.text_name.text or "").strip(),
      "type": (self.drop_down_cell_type.selected_value or "work_center").strip(),
      "active": bool(self.check_box_active.checked),
      "parallel_capacity": self._coerce_int(self.text_parallel_capacity.text, 1),
      "minute_cost_nz": self._coerce_float(self.text_minute_cost_nz.text, 0.0),
      "default_wip_bin_id": (self.text_default_wip_bin_id.text or "").strip() or None,
    }

    try:
      if self._is_new:
        # Generate an id if not present
        if not updated["_id"] or updated["_id"] == "(new)":
          updated["_id"] = anvil.server.call("generate_next_cell_id")
        saved = anvil.server.call("cells_create", updated) or updated
        self._is_new = False
      else:
        saved = anvil.server.call("cells_update", updated["_id"], updated) or updated

      self._cell = saved
      self._cell_id = saved.get("_id", updated["_id"])
      self._bind_fields()
      Notification("Saved.", style="success", timeout=1.5).show()

    except Exception as e:
      Notification(f"Save failed: {e}", style="danger").show()

  # ---------- Nav / delete ----------
  def button_back_click(self, **event_args):
    open_form("CellRecords")

  def button_delete_click(self, **event_args):
    cid = (self.label_cell_id.text or "").strip()
    if not cid:
      Notification("No cell id.", style="warning").show(); return
    if not confirm(f"Are you sure you want to delete cell '{cid}'?"):
      return
    try:
      anvil.server.call("cells_delete", cid)
      Notification("🗑️ Cell deleted.", style="danger").show()
      open_form("CellRecords")
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()

  # ---------- helpers ----------
  def _coerce_int(self, s, default=0):
    try:
      return int(str(s).strip() or default)
    except Exception:
      return int(default)

  def _coerce_float(self, s, default=0.0):
    try:
      return float(str(s).strip() or default)
    except Exception:
      return float(default)


