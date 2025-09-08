from anvil import *
import anvil.server
import datetime as _dt
import zoneinfo

_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")

class CellDetail(CellDetailTemplate):
  """
  Read-only cell header + operator task list.
  Props:
    cell_id: str  (required)
  """
  def __init__(self, cell_id: str, **properties):
    self.init_components(**properties)
    self._cell = None
    self._cell_id = cell_id
    self._load_cell()
    self._load_tasks()

  # -----------------------------
  # Cell header (read-only)
  # -----------------------------
  def _load_cell(self):
    try:
      c = anvil.server.call('cells_get', self._cell_id)
      if not c:
        Notification(f"Cell '{self._cell_id}' not found.", style="danger").show()
        self._bind_cell({})
        return
      self._cell = c
      self._bind_cell(c)
    except Exception as e:
      Notification(f"Failed to load cell: {e}", style="danger").show()
      self._bind_cell({})

  def _bind_cell(self, c: dict):
    self.label_cell_id.text      = c.get("_id","—")
    self.label_cell_name.text    = c.get("name","—")
    self.label_cell_type.text    = c.get("type","—")
    self.label_cell_active.text  = "Active" if c.get("active", True) else "Inactive"
    self.label_cell_capacity.text= str(int(c.get("parallel_capacity", 1)))
    self.label_cell_cost.text    = f"${float(c.get('minute_cost_nz',0.0)):.2f}/min"
    self.label_cell_wip_bin.text = c.get("default_wip_bin_id","—")

  # -----------------------------
  # Task list (operator view)
  # -----------------------------
  def _today_nz(self):
    return _dt.datetime.now(_NZ).date()

  def _calc_batch_run_time_min(self, task_row: dict) -> float | None:
    """
    Batch run-time (minutes for the whole lot) based on route op cycle time
    and this cell's parallel capacity.
    """
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      op = next((o for o in wo["route_ops"] if o["seq"] == task_row["operation_seq"]), None)
      if not op:
        return None
      cycle_time_min_per_unit = float(op["cycle_min_per_unit"])
      cap = int((self._cell or {}).get("parallel_capacity", 1)) or 1
      return round(task_row["qty"] * cycle_time_min_per_unit / cap, 1)
    except Exception:
      return None

  def _compute_next_and_due(self, task_row: dict):
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

  def _load_tasks(self):
    cell_id = self._cell_id
    if not cell_id:
      self.repeating_tasks.items = []
      self.label_task_summary.text = "No tasks."
      return

    try:
      # queued + in_progress + completed TODAY (NZ)
      items = anvil.server.call('tasks_for_cell_dashboard', cell_id, True)

      decorated = []
      today = self._today_nz()
      for t in (items or []):
        # Compute batch run-time
        batch_run_time_min = self._calc_batch_run_time_min(t)
        # Next destination
        next_cell_id, next_bin_id = self._compute_next_destination(t)
        # Priority bucket from scheduled_date
        sd = t.get("scheduled_date")  # date or None
        if sd and sd < today:
          bucket = "overdue";  bucket_label = "Overdue"
        elif sd == today:
          bucket = "today";    bucket_label = "Today"
        else:
          bucket = "upcoming"; bucket_label = "Upcoming"

        decorated.append({
          **t,
          "_op_name": f"OP{t.get('operation_seq')}",
          "batch_run_time_min": batch_run_time_min,
          "_bucket": bucket,
          "_bucket_label": bucket_label,
          "_scheduled_str": sd.isoformat() if sd else "—",
          "_next_cell_id": next_cell_id or "-",
          "_next_bin_id": next_bin_id or "-",
        })

      # sort: bucket → scheduled_date → priority → op seq
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






