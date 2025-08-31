from anvil import *
import anvil.server
import datetime as _dt
import zoneinfo
_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")  # keep UI in shop TZ

class CellDetail(CellDetailTemplate):
  """
  Props:
    cell_id: str | None  # if None, a new _id is generated on init
  """
  def __init__(self, cell_id: str | None = None, **properties):
    self.init_components(**properties)
    self._cell = None
    self._is_new = (cell_id is None)
    self._load_cell(cell_id)
    self._load_tasks()

  # -----------------------------
  # Loading & Binding
  # -----------------------------
  def _load_cell(self, cell_id):
    if cell_id:
      self._cell = anvil.server.call('cells_get', cell_id)
      self._is_new = False
      if not self._cell:
        Notification(f"Cell '{cell_id}' not found.", style="danger").show()
        self._cell = self._new_cell_doc()
        self._is_new = True
    else:
      self._cell = self._new_cell_doc()
      self._is_new = True

    self._bind_form()

  def _new_cell_doc(self) -> dict:
    new_id = anvil.server.call('generate_next_cell_id')
    return {
      "_id": new_id,
      "name": "",
      "type": "work_center",
      "active": True,
      "parallel_capacity": 1,
      "minute_cost_nz": 1.0,
      "default_wip_bin_id": ""
    }

  def _bind_form(self):
    c = self._cell or {}
    self.lbl_id.text = c.get("_id","")
    self.txt_name.text = c.get("name","")
    self.dd_type.selected_value = c.get("type","work_center")
    self.chk_active.checked = bool(c.get("active", True))
    self.num_capacity.value = int(c.get("parallel_capacity", 1))
    self.num_cost.value = float(c.get("minute_cost_nz", 1.0))
    self.txt_wip_bin.text = c.get("default_wip_bin_id","")

  # -----------------------------
  # Persist
  # -----------------------------
  def _collect_payload(self) -> dict:
    if not (self.txt_name.text or "").strip():
      Notification("Cell name is required.", style="danger").show()
      raise ValueError("Cell name required")
    if not (self.txt_wip_bin.text or "").strip():
      Notification("Default WIP bin is required.", style="danger").show()
      raise ValueError("WIP bin required")

    return {
      "_id": self.lbl_id.text,
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
      self.btn_save.enabled = False
      self.btn_delete.enabled = False
      for c in [self.txt_name, self.dd_type, self.chk_active,
                self.num_capacity, self.num_cost, self.txt_wip_bin]:
        c.enabled = False
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()

  # -----------------------------
  # Tasks (right pane)
  # -----------------------------
  def _today_nz(self):
    return _dt.datetime.now(_NZ).date()

  def _load_tasks(self):
    cell_id = (self.lbl_id.text or "").strip()
    if not cell_id:
      self.repeating_tasks.items = []
      self.lbl_task_summary.text = "No tasks (unsaved cell)."
      return
  
    try:
      # 1) fetch ALL tasks (no date filter)
      items = anvil.server.call('tasks_list_for_cell', cell_id, None, None)  # all statuses; adjust to status="queued" if desired
  
      # 2) decorate with batch_run_time_min and date buckets
      decorated = []
      today = self._today_nz()
      for t in (items or []):
        op_name = f"OP{t.get('operation_seq')}"
        batch_run_time_min = self._calc_batch_run_time_min(t)
        sd = t.get("scheduled_date")  # expects a date
        # bucket
        if sd and sd < today:
          bucket = "overdue"
        elif sd == today:
          bucket = "today"
        else:
          bucket = "upcoming"
        decorated.append({**t,
                          "_op_name": op_name,
                          "batch_run_time_min": batch_run_time_min,
                          "_bucket": bucket})
  
      # 3) optional filter: today only
      if self.chk_today_only.checked:
        decorated = [d for d in decorated if d.get("_bucket") in ("overdue", "today")]  # keep overdue visible
  
      # 4) sort by (bucket order) then scheduled_date, then priority, then op seq
      bucket_order = {"overdue": 0, "today": 1, "upcoming": 2}
      decorated.sort(key=lambda d: (
        bucket_order.get(d.get("_bucket"), 3),
        d.get("scheduled_date") or _dt.date.max,
        int(d.get("priority", 999)),
        int(d.get("operation_seq", 999)),
      ))
  
      self.repeating_tasks.items = decorated
  
      # 5) header summary
      n_over = sum(1 for d in decorated if d["_bucket"] == "overdue")
      n_today = sum(1 for d in decorated if d["_bucket"] == "today")
      n_up = sum(1 for d in decorated if d["_bucket"] == "upcoming")
      if self.chk_today_only.checked:
        self.lbl_task_summary.text = f"{n_over} overdue • {n_today} today"
      else:
        self.lbl_task_summary.text = f"{n_over} overdue • {n_today} today • {n_up} upcoming"
  
    except Exception as e:
      self.lbl_task_summary.text = f"Failed to load tasks: {e}"
      self.repeating_tasks.items = []

  def _decorate_tasks(self, items):
    decorated = []
    for t in (items or []):
      op_name = f"OP{t.get('operation_seq')}"
      batch_run_time_min = self._calc_batch_run_time_min(t)
      decorated.append({**t,
                        "_op_name": op_name,
                        "batch_run_time_min": batch_run_time_min})
    return decorated

  def _calc_batch_run_time_min(self, task_row: dict) -> float | None:
    """
    Calculate estimated batch run-time (minutes for the whole lot)
    based on cycle time, qty, and parallel capacity.
    """
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      op = next((o for o in wo["route_ops"]
                 if o["seq"] == task_row["operation_seq"]), None)
      if not op:
        return None
      cycle_time_min_per_unit = float(op["cycle_min_per_unit"])
      cap = int(self.num_capacity.value or 1)
      return round(task_row["qty"] * cycle_time_min_per_unit / cap, 1)
    except Exception:
      return None

  def btn_refresh_tasks_click(self, **event_args):
    self._load_tasks()

  def task_start_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_start', row_data["_id"])
      self._load_tasks()
    except Exception as e:
      Notification(f"Start failed: {e}", style="danger").show()

  def task_complete_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_complete', row_data["_id"])
      self._load_tasks()
    except Exception as e:
      Notification(f"Complete failed: {e}", style="danger").show()

  def chk_today_only_change(self, **event_args):
    self._load_tasks()



