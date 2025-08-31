# Form: CellDetail
# File: client_code/CellDetail/__init__.py

from anvil import *
import anvil.server
import datetime as _dt

class CellDetail(CellDetailTemplate):
  """
  Props:
    cell_id: str | None
  """
  def __init__(self, cell_id: str | None = None, **properties):
    self.init_components(**properties)
    self._cell = None
    self._is_new = cell_id is None
    self._load_cell(cell_id)
    self._load_tasks_for_today()

  # -----------------------------
  # Loading & Binding
  # -----------------------------
  def _load_cell(self, cell_id):
    if cell_id:
      self._cell = anvil.server.call('cells_get', cell_id)
      self._is_new = False
    else:
      # sensible defaults for new cell
      self._cell = {
        "_id": "",
        "name": "",
        "type": "work_center",
        "active": True,
        "parallel_capacity": 1,
        "minute_cost_nz": 1.0,
        "default_wip_bin_id": ""
      }
      self._is_new = True

    self._bind_form()

  def _bind_form(self):
    c = self._cell or {}
    self.txt_id.text = c.get("_id","")
    self.txt_name.text = c.get("name","")
    self.dd_type.selected_value = c.get("type","work_center")
    self.chk_active.checked = bool(c.get("active", True))
    self.num_capacity.value = int(c.get("parallel_capacity", 1))
    self.num_cost.value = float(c.get("minute_cost_nz", 1.0))
    self.txt_wip_bin.text = c.get("default_wip_bin_id","")

    # New cells: id is editable; existing: lock id
    self.txt_id.enabled = self._is_new

  # -----------------------------
  # Persist
  # -----------------------------
  def _collect_payload(self) -> dict:
    # Basic validation
    if not (self.txt_id.text or "").strip():
      Notification("Cell ID is required.", style="danger").show()
      raise ValueError("Cell ID required")
    if not (self.txt_name.text or "").strip():
      Notification("Cell name is required.", style="danger").show()
      raise ValueError("Cell name required")
    if not (self.txt_wip_bin.text or "").strip():
      Notification("Default WIP bin is required.", style="danger").show()
      raise ValueError("WIP bin required")

    return {
      "_id": self.txt_id.text.strip().upper().replace(" ", "-"),
      "name": self.txt_name.text.strip(),
      "type": self.dd_type.selected_value or "work_center",
      "active": bool(self.chk_active.checked),
      "parallel_capacity": int(self.num_capacity.value or 1),
      "minute_cost_nz": float(self.num_cost.value or 0.0),
      "default_wip_bin_id": self.txt_wip_bin.text.strip()
    }

  def btn_save_click(self, **event_args):
    try:
      payload = self._collect_payload()
      if self._is_new:
        saved = anvil.server.call('cells_create', payload)
        self._cell = saved
        self._is_new = False
        self.txt_id.enabled = False
        Notification("Cell created.", style="success").show()
      else:
        saved = anvil.server.call('cells_update', self._cell["_id"], payload)
        self._cell = saved
        Notification("Cell updated.", style="success").show()
    except Exception as e:
      Notification(f"Save failed: {e}", style="danger", timeout=6).show()

  def btn_delete_click(self, **event_args):
    if self._is_new:
      Notification("Nothing to delete (new, unsaved).", style="warning").show()
      return
    if not confirm(f"Delete cell {self._cell['_id']}? This cannot be undone."):
      return
    try:
      anvil.server.call('cells_delete', self._cell["_id"])
      Notification("Cell deleted.", style="success").show()
      # Optional: close or navigate away; here we just disable editing
      self.btn_save.enabled = False
      self.btn_delete.enabled = False
      for c in [self.txt_id, self.txt_name, self.dd_type, self.chk_active, self.num_capacity, self.num_cost, self.txt_wip_bin]:
        c.enabled = False
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()

  # -----------------------------
  # Tasks (right pane)
  # -----------------------------
  def _today(self):
    # your app is NZ based; the client timezone will do for UI
    return _dt.date.today()

  def _load_tasks_for_today(self):
    # Guard for new cells
    if not self.txt_id.text.strip():
      self.repeating_tasks.items = []
      self.lbl_task_summary.text = "No tasks (unsaved cell)."
      return

    try:
      items = anvil.server.call('tasks_list_for_cell', self.txt_id.text.strip(), self._today(), None)
      self.repeating_tasks.items = self._decorate_tasks(items)
      self.lbl_task_summary.text = f"{len(items)} task(s) scheduled today"
    except Exception as e:
      self.lbl_task_summary.text = f"Failed to load tasks: {e}"
      self.repeating_tasks.items = []

  def _decorate_tasks(self, items):
    # attach op_name and est_run_min for better display
    dec = []
    for t in (items or []):
      op_name = f"OP{t.get('operation_seq')}"
      est = self._estimate_task_minutes(t)
      dec.append({**t, "_op_name": op_name, "_est_min": est})
    return dec

  def _estimate_task_minutes(self, task_row: dict) -> float | None:
    # Simple estimate: qty / (rate * cap). We need the op's cycle time.
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      op = next((o for o in wo["route_ops"] if o["seq"] == task_row["operation_seq"]), None)
      if not op:
        return None
      rate = 1.0 / float(op["cycle_min_per_unit"])
      # capacity here should be the cell's; we have it in the form
      cap = int(self.num_capacity.value or 1)
      return round(task_row["qty"] / (rate * cap), 1)
    except Exception:
      return None

  def btn_refresh_tasks_click(self, **event_args):
    self._load_tasks_for_today()

  def task_start_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_start', row_data["_id"])
      self._load_tasks_for_today()
    except Exception as e:
      Notification(f"Start failed: {e}", style="danger").show()

  def task_complete_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_complete', row_data["_id"])
      self._load_tasks_for_today()
    except Exception as e:
      Notification(f"Complete failed: {e}", style="danger").show()

