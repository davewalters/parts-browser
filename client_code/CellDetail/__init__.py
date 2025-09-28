from anvil import *
import anvil.server
import datetime as _dt
import zoneinfo

from ._anvil_designer import CellDetailTemplate
from ..CellTaskRow import CellTaskRow

_TZ_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")

class CellDetail(CellDetailTemplate):
  def __init__(self, cell_id: str, **properties):
    self.init_components(**properties)
    self._cell_id = str(cell_id or "").strip()
    self._cell = None

    self.repeating_tasks.item_template = CellTaskRow
    self.repeating_tasks.set_event_handler("x-task-start-resume", self._on_start_resume)
    self.repeating_tasks.set_event_handler("x-task-pause", self._on_pause)
    self.repeating_tasks.set_event_handler("x-task-finish", self._on_finish)
    self.repeating_tasks.set_event_handler("x-task-issue", self._on_issue)
    self.repeating_tasks.set_event_handler("x-task-pick", self._on_pick)

    self._load_cell()
    self._load_tasks()

  # ---------- Header ----------
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

  # ---------- Helpers ----------
  def _today_nz(self):
    return _dt.datetime.now(_TZ_NZ).date()

  def _calc_batch_run_time_min(self, task_row: dict) -> float | None:
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"])
      op = next((o for o in wo.get("route_ops", []) if o.get("seq") == task_row.get("operation_seq")), None)
      if not op: return None
      cycle = float(op.get("cycle_min_per_unit") or 0.0)
      cap = int((self._cell or {}).get("parallel_capacity", 1)) or 1
      if cycle <= 0 or cap <= 0: return None
      return round(task_row.get("qty", 0) * cycle / cap, 1)
    except Exception:
      return None

  def _compute_next_destination(self, task_row: dict):
    try:
      wo = anvil.server.call('wo_get', task_row["wo_id"]) or {}
      wo_due = wo.get("due_date")
      ops = sorted(wo.get("route_ops", []), key=lambda o: o.get("seq", 999999))
      seq = task_row.get("operation_seq")
      idx = next((i for i,o in enumerate(ops) if o.get("seq") == seq), None)
      if idx is None or idx >= len(ops) - 1:
        return None, None, wo_due
      next_op = ops[idx + 1]
      next_cell_id = next_op.get("cell_id")
      next_cell = anvil.server.call('cells_get', next_cell_id) if next_cell_id else None
      next_bin_id = (next_cell or {}).get("default_wip_bin_id")
      return next_cell_id, next_bin_id, wo_due
    except Exception:
      return None, None, None

  def _decorate_material_readiness(self, row: dict) -> None:
    """
    Enrich a task row with material readiness for this step.
    Uses wobom_get_lines(wo_id) and filters by issue_seq == op seq.
    Produces:
      row["_mat_state"] in {"ready","partial","short"}
      row["_mat_summary"] list with {part_id, req, res, short, status}
      row["_mat_hint"] short tooltip string
    """
    try:
      seq = row.get("operation_seq")
      wobom = anvil.server.call("wobom_get_lines", row.get("wo_id")) or []
      step_lines = [ln for ln in wobom if (ln.get("issue_seq") == seq)]
      summary = []
      all_ready = True
      any_reserved = False

      for ln in step_lines:
        req = float(ln.get("qty_required", 0.0) or 0.0)
        reservations = ln.get("reservations") or []
        res = sum(float(r.get("qty", 0.0) or 0.0) for r in reservations)
        short = max(0.0, req - res)
        status = "ready" if res >= req - 1e-9 else ("partial" if res > 0 else "short")
        all_ready = all_ready and (status == "ready")
        any_reserved = any_reserved or (res > 0)
        summary.append({
          "part_id": ln.get("part_id"),
          "req": req,
          "res": res,
          "short": short,
          "status": status
        })

      if not step_lines:
        # no mapped materials → consider step "ready" (nothing to pick)
        state = "ready"
      elif all_ready:
        state = "ready"
      elif any_reserved:
        state = "partial"
      else:
        state = "short"

      row["_mat_state"] = state
      row["_mat_summary"] = summary

      # Build a compact tooltip
      tops = summary[:5]
      hint_lines = [f"{s['part_id']}: req {s['req']:.3g}, res {s['res']:.3g}" + (f", short {s['short']:.3g}" if s['short']>0 else "")
                    for s in tops]
      more = f" …(+{len(summary)-5} more)" if len(summary) > 5 else ""
      row["_mat_hint"] = "\n".join(hint_lines) + more if hint_lines else "No mapped materials."
    except Exception:
      row["_mat_state"] = "short"
      row["_mat_summary"] = []
      row["_mat_hint"] = "Material status unavailable."

  # ---------- Load ----------
  def _load_tasks(self):
    if not self._cell_id:
      self.repeating_tasks.items = []
      self.label_task_summary.text = "No tasks."
      return

    try:
      items = anvil.server.call('tasks_for_cell_dashboard', self._cell_id, True) or []
      decorated = []
      today = self._today_nz()

      for t in items:
        # compute run time
        t["batch_run_time_min"] = self._calc_batch_run_time_min(t)
        # next hop
        nxt_cell, nxt_bin, _ = self._compute_next_destination(t)
        t["_next_cell_id"] = nxt_cell or "-"
        t["_next_bin_id"]  = nxt_bin or "-"
        # schedule bucket
        sd = t.get("scheduled_date")
        t["_scheduled_str"] = sd.isoformat() if isinstance(sd, _dt.date) else "—"
        if isinstance(sd, _dt.date) and sd < today:
          t["_bucket"] = "overdue"
        elif sd == today:
          t["_bucket"] = "today"
        else:
          t["_bucket"] = "upcoming"
        # material readiness (new)
        self._decorate_material_readiness(t)

        decorated.append(t)

      bucket_order = {"overdue": 0, "today": 1, "upcoming": 2}
      decorated.sort(key=lambda d: (
        bucket_order.get(d.get("_bucket"), 3),
        d.get("scheduled_date") or _dt.date.max,
        int(d.get("priority", 999)),
        int(d.get("operation_seq", 999)),
      ))
      self.repeating_tasks.items = decorated

      n_over = sum(1 for d in decorated if d.get("_bucket") == "overdue")
      n_today = sum(1 for d in decorated if d.get("_bucket") == "today")
      n_up = sum(1 for d in decorated if d.get("_bucket") == "upcoming")
      self.label_task_summary.text = f"{n_over} overdue • {n_today} today • {n_up} upcoming"

    except Exception as e:
      self.label_task_summary.text = f"Failed to load tasks: {e}"
      self.repeating_tasks.items = []

  # Toolbar
  def button_refresh_tasks_click(self, **e):
    self._load_tasks()

  # ---------- Row actions ----------
  def _on_start_resume(self, row: dict, **e):
    try:
      # If not ready, give the operator a heads-up, but still allow start if they insist.
      if (row.get("_mat_state") or "short") != "ready":
        if not confirm("Materials are not fully picked for this step. Start anyway?"):
          return
      anvil.server.call('tasks_start', row.get("_id"))
      self._load_tasks()
    except Exception as ex:
      Notification(f"Start/Resume failed: {ex}", style="danger").show()

  def _on_pause(self, row: dict, **e):
    try:
      anvil.server.call('tasks_pause', row.get("_id"))
      Notification("Paused.", timeout=2).show()
      self._load_tasks()
    except Exception as ex:
      Notification(f"Pause failed: {ex}", style="danger").show()

  def _on_finish(self, row: dict, **e):
    try:
      # Flow complete handles: consume materials for this op + move output to next bin/FG
      anvil.server.call('tasks_complete', row.get("_id"))
      nxt_cell, nxt_bin, _ = self._compute_next_destination(row)
      if nxt_cell and nxt_bin:
        Notification(f"Finished. Next: {nxt_cell} → {nxt_bin}", timeout=4).show()
      else:
        Notification("Finished. This was the last operation.", timeout=4).show()
      self._load_tasks()
    except Exception as ex:
      Notification(f"Finish failed: {ex}", style="danger").show()

  def _on_issue(self, row: dict, **e):
    """
    Coarse ‘Issue’: commit all reservations for this WO (WO-wide).
    If you later add a per-step API, we’ll switch to committing only issue_seq==op seq.
    """
    try:
      res = anvil.server.call("wo_commit_all_picks", row.get("wo_id")) or {}
      Notification(f"Issued: consumed {res.get('consumed',0)} lines, skipped {res.get('skipped',0)}.", timeout=3).show()
      self._load_tasks()
    except Exception as ex:
      Notification(f"Issue failed: {ex}", style="danger").show()

  def _on_pick(self, row: dict, **e):
    """
    Generate a picklist (by destination) for this WO and let the operator know.
    You can route to a PicklistRecord here if you prefer.
    """
    try:
      pl = anvil.server.call("flow_generate_picklist_by_destination", row.get("wo_id")) or {}
      pid = pl.get("_id","(new)")
      Notification(f"Picklist {pid} generated. You can open Picklists to action it.", timeout=4).show()
      open_form("PicklistRecord", picklist_id=pid)
      self._load_tasks()
    except Exception as ex:
      Notification(f"Pick failed: {ex}", style="danger").show()







