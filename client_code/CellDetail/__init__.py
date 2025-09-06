from anvil import *
import anvil.server
import datetime as _dt
import zoneinfo
_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")  # keep UI in shop TZ

class CellDetail(CellDetailTemplate):
  """
  Props:
    cell_id: str | None
  """
  def __init__(self, cell_id: str | None = None, **properties):
    self.init_components(**properties)
    self._cell = None
    self._is_new = (cell_id is None)

    self.drop_down_type.items = [
      ("Work Centre", "work_center"),
      ("Assembly", "assembly"),
      ("Inspection", "inspection"),
      ("Packout", "packout"),
      ("Test", "test"),
      ("Other", "other"),
    ]
    self.button_back.role = "mydefault-button"
    self.button_save_cell.role = "save-button"
    self.button_delete_cell.role = "delete-button"
    self.button_refresh_tasks.role = "new-button"

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
    self.label_id.text = c.get("_id","")
    self.text_cell_name.text = c.get("name","")
    self.drop_down_type.selected_value = c.get("type","work_center")
    self.check_box_active.checked = bool(c.get("active", True))
    self.num_capacity.value = int(c.get("parallel_capacity", 1))
    self.num_cost.value = float(c.get("minute_cost_nz", 1.0))
    self.text_cell_bin_id.text = c.get("default_wip_bin_id","")

  # -----------------------------
  # Persist
  # -----------------------------
  def _collect_payload(self) -> dict:
    if not (self.text_cell_name.text or "").strip():
      Notification("Cell name is required.", style="danger").show()
      raise ValueError("Cell name required")
    if not (self.text_cell_bin_id.text or "").strip():
      Notification("Default Cell WIP bin is required.", style="danger").show()
      raise ValueError("Cell WIP bin required")

    return {
      "_id": self.label_id.text,
      "name": self.text_cell_name.text.strip(),
      "type": self.drop_down_type.selected_value or "work_center",
      "active": bool(self.check_box_active.checked),
      "parallel_capacity": int(self.num_capacity.value or 1),
      # FIX: use num_cost.value (was text_runtime_cost)
      "minute_cost_nz": float(self.num_cost.value or 0.0),
      "default_wip_bin_id": self.text_cell_bin_id.text.strip()
    }

  def button_save_cell_click(self, **event_args):
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

  def button_delete_cell_click(self, **event_args):
    if self._is_new:
      Notification("Nothing to delete (new, unsaved).", style="warning").show()
      return
    if not confirm(f"Delete cell {self._cell['_id']}? This cannot be undone."):
      return
    try:
      anvil.server.call('cells_delete', self._cell["_id"])
      Notification("Cell deleted.", style="success").show()
      # Disable inputs cleanly
      for c in [self.text_cell_name, self.drop_down_type, self.check_box_active,
                self.num_capacity, self.num_cost, self.text_cell_bin_id,
                self.button_save_cell, self.button_delete_cell]:
        c.enabled = False
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()

  # -----------------------------
  # Tasks (right pane)
  # -----------------------------
  def _today_nz(self):
    return _dt.datetime.now(_NZ).date()

  def _load_tasks(self):
    cell_id = (self.label_id.text or "").strip()
    if not cell_id:
      self.repeating_tasks.items = []
      self.label_task_summary.text = "No tasks (unsaved cell)."
      return

    try:
      items = anvil.server.call('tasks_for_cell_dashboard', cell_id, True)

      decorated = []
      today = self._today_nz()
      for t in (items or []):
        op_name = f"OP{t.get('operation_seq')}"
        batch_run_time_min = self._calc_batch_run_time_min(t)

        # Next destination + WO due date
        next_cell_id, next_bin_id, wo_due_date = self._compute_next_and_due(t)

        # Bucket & label
        sd = t.get("scheduled_date")  # date or None
        if sd and sd < today:
          bucket = "overdue";  bucket_label = "Overdue"
        elif sd == today:
          bucket = "today";    bucket_label = "Today"
        else:
          bucket = "upcoming"; bucket_label = "Upcoming"

        decorated.append({
          **t,
          "_op_name": op_name,
          "batch_run_time_min": batch_run_time_min,
          "_bucket": bucket,
          "_bucket_label": bucket_label,
          "_scheduled_str": sd.isoformat() if sd else "—",
          "_next_cell_id": next_cell_id or "-",
          "_next_bin_id": next_bin_id or "-",
          "_wo_due_str": wo_due_date.isoformat() if wo_due_date else "—",
        })

      bucket_order = {"overdue": 0, "today": 1, "upcoming": 2}
      decorated.sort(key=lambda d: (
        bucket_order.get(d.get("_bucket"), 3),
        d.get("scheduled_date") or _dt.date.max,
        int(d.get("priority", 999)),
        int(d.get("operation_seq", 999)),
      ))
      self.repeating_tasks.items = decorated

      n_over = sum(1 for d in decorated if d["_bucket"] == "overdue")
      n_today = sum(1 for d in decorated if d["_bucket"] == "today")
      n_up = sum(1 for d in decorated if d["_bucket"] == "upcoming")
      self.label_task_summary.text = f"{n_over} overdue • {n_today} today • {n_up} upcoming"

    except Exception as e:
      self.label_task_summary.text = f"Failed to load tasks: {e}"
      self.repeating_tasks.items = []

  def _compute_next_and_due(self, task_row: dict):
    """
    Returns (next_cell_id, next_bin_id, wo_due_date or None).
    """
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      wo_due = wo.get("due_date")
      ops = sorted(wo.get("route_ops", []), key=lambda o: o["seq"])
      seq = task_row.get("operation_seq")
      idx = next((i for i,o in enumerate(ops) if o["seq"] == seq), None)
      if idx is None or idx >= len(ops) - 1:
        return None, None, wo_due
      next_op = ops[idx + 1]
      next_cell = anvil.server.call('cells_get', next_op["cell_id"])
      next_bin = (next_cell or {}).get("default_wip_bin_id")
      return next_op["cell_id"], next_bin, wo_due
    except Exception:
      return None, None, None

  def _calc_batch_run_time_min(self, task_row: dict) -> float | None:
    """
    Estimate batch time (min) = qty * cycle / parallel_capacity
    """
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      op = next((o for o in wo["route_ops"] if o["seq"] == task_row["operation_seq"]), None)
      if not op:
        return None
      cycle_time_min_per_unit = float(op.get("cycle_min_per_unit", 0.0))
      cap = int(self.num_capacity.value or 1)
      return round((task_row.get("qty", 0) * cycle_time_min_per_unit) / max(cap, 1), 1)
    except Exception:
      return None

  def button_refresh_tasks_click(self, **event_args):
    self._load_tasks()

  # -----------------------------
  # Task commands from row
  # -----------------------------
  def task_start_or_resume_click(self, row_data, **event_args):
    try:
      st = (row_data.get("status") or "queued").lower()
      if st == "paused":
        anvil.server.call('tasks_resume', row_data["_id"])
      else:
        anvil.server.call('tasks_start', row_data["_id"])
      self._load_tasks()
    except Exception as e:
      Notification(f"Start/Resume failed: {e}", style="danger").show()

  def task_pause_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_pause', row_data["_id"])
      Notification("Paused.", timeout=2).show()
      self._load_tasks()
    except Exception as e:
      Notification(f"Pause failed: {e}", style="danger").show()

  def task_finish_click(self, row_data, **event_args):
    try:
      anvil.server.call('tasks_complete', row_data["_id"])
      next_cell_id, next_bin_id, _ = self._compute_next_and_due(row_data)
      if next_cell_id and next_bin_id:
        Notification(f"Finished. Next: {next_cell_id} → {next_bin_id}", timeout=4).show()
      else:
        Notification("Finished. This was the last operation.", timeout=4).show()
      self._load_tasks()
    except Exception as e:
      Notification(f"Finish failed: {e}", style="danger").show()





