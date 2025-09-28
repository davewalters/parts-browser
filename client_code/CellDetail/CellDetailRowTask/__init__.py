# client_code/CellDetailRowTask/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import CellDetailRowTaskTemplate

class CellDetailRowTask(CellDetailRowTaskTemplate):
  """
  Expects self.item with keys populated by CellDetail parent:
    {
      "_id": "TASK-...",
      "wo_id": "...",
      "operation_seq": int,
      "qty": int,
      "status": "queued|in_progress|paused|done",
      "priority": int,
      "_scheduled_str": "YYYY-MM-DD" or "—",
      "_next_cell_id": "...",
      "_next_bin_id": "...",
      "batch_run_time_min": float|None
    }
  The parent form (CellDetail) maintains _wobom_cache: dict[wo_id] -> list[WOBOM lines]
  """

  def __init__(self, **properties):
    self.init_components(**properties)
    # Button roles (optional)
    self.button_start_resume.role = "mydefault-button"
    self.button_pause.role        = "delete-button"
    self.button_finish.role       = "save-button"
    self.button_pick.role         = "secondary-button"  # Comment out if you hide Pick

  # ---------- UI bind ----------
  def form_show(self, **event_args):
    d = dict(self.item or {})

    # Labels per your naming convention
    self.label_priority.text        = str(d.get("priority", ""))
    self.label_wo_id.text           = d.get("wo_id", "—")
    self.label_op_name.text         = f"OP{d.get('operation_seq')}"
    self.label_qty.text             = str(d.get("qty", ""))
    self.label_status.text          = (d.get("status") or "").replace("_", " ").title()
    self.label_scheduled_date.text  = d.get("_scheduled_str", "—")
    self.label_next_cell.text       = d.get("_next_cell_id", "-")
    self.label_next_bin.text        = d.get("_next_bin_id", "-")

    brt = d.get("batch_run_time_min")
    self.label_batch_runtime.text   = f"{brt:.1f} min" if isinstance(brt, (int, float)) else "—"

    # Compute readiness immediately
    self._refresh_material_readiness()

    # Button enablement
    st = (d.get("status") or "queued").lower()
    self.button_start_resume.enabled = st in ("queued", "paused")
    self.button_pause.enabled        = st == "in_progress"
    self.button_finish.enabled       = st in ("in_progress", "paused")
    # Pick is always allowed (it just creates reservations); hide if you prefer
    self.button_pick.visible         = True   # set False to hide in UI

  # ---------- Readiness (row-level, cached) ----------
  def _refresh_material_readiness(self):
    """
    Row-level readiness using parent cache:
      - Sum qty_required for WOBOM lines where issue_seq == this op
      - Sum reserved qty from reservations
      - Set label_materials_status + label_materials_detail
    """
    parent = self.parent
    if not hasattr(parent, "_wobom_cache"):
      parent._wobom_cache = {}

    wo_id = (self.item or {}).get("wo_id")
    op_seq = int((self.item or {}).get("operation_seq") or 0)

    if wo_id not in parent._wobom_cache:
      try:
        parent._wobom_cache[wo_id] = anvil.server.call("wobom_get_lines", wo_id) or []
      except Exception:
        parent._wobom_cache[wo_id] = []

    lines = parent._wobom_cache.get(wo_id, [])
    at_step = [ln for ln in lines if int(ln.get("issue_seq") or 0) == op_seq]

    req = sum(float(ln.get("qty_required", 0) or 0.0) for ln in at_step)
    reserved = 0.0
    for ln in at_step:
      for r in (ln.get("reservations") or []):
        reserved += float(r.get("qty", 0) or 0.0)

    if not at_step or req <= 0:
      status = "ready"
      detail = "No external materials required"
    elif reserved >= req - 1e-6:
      status = "ready"
      detail = f"Reserved {reserved:.3g}/{req:.3g}"
    elif reserved > 0:
      status = "partial"
      detail = f"Reserved {reserved:.3g}/{req:.3g} (short {max(0.0, req - reserved):.3g})"
    else:
      status = "short"
      detail = f"Reserved 0/{req:.3g}"

    # Paint the pill (very light styling here; adapt to your roles/theme)
    self.label_materials_status.text = status.upper()
    self.label_materials_detail.text = detail
    self._apply_status_style(status)

  def _apply_status_style(self, status: str):
    st = (status or "").lower()
    # You can swap to roles (e.g., "status-ready", "status-partial", "status-short")
    if st == "ready":
      self.label_materials_status.foreground = "#0a7d12"  # green
    elif st == "partial":
      self.label_materials_status.foreground = "#b8860b"  # dark goldenrod
    elif st == "short":
      self.label_materials_status.foreground = "#b00020"  # red
    else:
      self.label_materials_status.foreground = None

  # ---------- Buttons ----------
  def button_start_resume_click(self, **event_args):
    row = dict(self.item or {})
    try:
      st = (row.get("status") or "queued").lower()
      if st == "paused":
        anvil.server.call("tasks_resume", row.get("_id"))
      else:
        anvil.server.call("tasks_start", row.get("_id"))
      Notification("Started.", timeout=2).show()
      # parent reload updates times + enables/disables
      self.parent._load_tasks()
    except Exception as e:
      alert(f"Start failed: {e}")

  def button_pause_click(self, **event_args):
    row = dict(self.item or {})
    try:
      anvil.server.call("tasks_pause", row.get("_id"))
      Notification("Paused.", timeout=2).show()
      self.parent._load_tasks()
    except Exception as e:
      alert(f"Pause failed: {e}")

  def button_finish_click(self, **event_args):
    """
    Finish consumes external materials mapped to this op (via reservations or immediate),
    then auto-transfers WIP to the next cell (or produces FG at last step).
    """
    row = dict(self.item or {})
    try:
      anvil.server.call("tasks_complete", row.get("_id"))
      Notification("Finished.", timeout=2).show()
      # Invalidate WOBOM cache for this WO so downstream rows see the change
      wo_id = row.get("wo_id")
      if hasattr(self.parent, "_wobom_cache") and wo_id in self.parent._wobom_cache:
        del self.parent._wobom_cache[wo_id]
      self.parent._load_tasks()
    except Exception as e:
      alert(f"Finish failed: {e}")

  def button_pick_click(self, **event_args):
    """
    Optional: create reservations via a picklist so this step becomes 'ready'.
    We generate per-operation picklists (group_by='operation') for the WO;
    that will reserve lines for all steps, but it still helps operators on this step.
    If you prefer to limit reservations strictly to this step, we can add a
    server helper later (e.g., flow.reserve_for_step(wo_id, op_seq)).
    """
    row = dict(self.item or {})
    wo_id = row.get("wo_id")
    try:
      # generate per-operation picklists for this WO
      anvil.server.call("picklist_generate", wo_id, "operation")
      # refresh cache & readiness
      if hasattr(self.parent, "_wobom_cache") and wo_id in self.parent._wobom_cache:
        del self.parent._wobom_cache[wo_id]
      self._refresh_material_readiness()
      Notification("Picklist generated / reservations attempted.", timeout=3).show()
    except Exception as e:
      alert(f"Pick failed: {e}")






