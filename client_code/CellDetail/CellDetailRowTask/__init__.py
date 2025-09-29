# client_code/CellDetailRowTask/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import CellDetailRowTaskTemplate

class CellDetailRowTask(CellDetailRowTaskTemplate):
  """
  self.item (populated by CellDetail) example:
    {
      "_id": "TASK-...",
      "wo_id": "...",
      "operation_seq": 20,
      "qty": 5,
      "status": "queued|in_progress|paused|done",
      "priority": 3,
      "_scheduled_str": "YYYY-MM-DD" or "—",
      "_next_cell_id": "CELL-B",
      "_next_bin_id": "BIN-B-WIP",
      "batch_run_time_min": 12.0
    }
  Parent (CellDetail) may keep: self._wobom_cache: dict[wo_id] -> list[WOBOM lines]
  """

  def __init__(self, **properties):
    self.init_components(**properties)
    # Button roles (optional)
    self.button_start_resume.role = "mydefault-button"
    self.button_pause.role        = "delete-button"
    self.button_finish.role       = "save-button"

    # We’re hiding Pick (relying on Finish to consume)
    if hasattr(self, "button_pick"):
      self.button_pick.visible = False

  # ---------- UI bind ----------
  def form_show(self, **event_args):
    d = dict(self.item or {})

    # 1) Header/fields (priority first)
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

    # 2) Material readiness (row-level; cached by parent)
    state, detail = self._compute_material_readiness(d)    # "ready"|"partial"|"short"|"na", and detail
    self.label_materials_status.text = state.title()
    #self.label_materials_detail.text = detail or ""
    self._apply_material_led(state)

    # 3) Button enablement
    st = (d.get("status") or "queued").lower()
    self.button_start_resume.enabled = st in ("queued", "paused")
    self.button_pause.enabled        = st == "in_progress"
    self.button_finish.enabled       = st in ("in_progress", "paused")

  # ---------- Readiness helpers ----------
  def _compute_material_readiness(self, row: dict) -> tuple[str, str]:
    """
    Uses parent._wobom_cache (fetches once per WO) and summarizes materials
    required at this step vs reserved.
    Returns: (state, detail)
    """
    parent = self.parent
    if not hasattr(parent, "_wobom_cache"):
      parent._wobom_cache = {}

    wo_id = row.get("wo_id")
    op_seq = int(row.get("operation_seq") or 0)

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

    # No external materials → Ready
    if not at_step or req <= 0:
      return "ready", "No external materials required"

    eps = 1e-6
    if reserved >= req - eps:
      return "ready", f"Reserved {reserved:.3g}/{req:.3g}"
    if reserved > 0:
      short = max(0.0, req - reserved)
      return "partial", f"Reserved {reserved:.3g}/{req:.3g} (short {short:.3g})"
    return "short", f"Reserved 0/{req:.3g}"

  def _apply_material_led(self, state: str):
    """Map readiness → LED role (requires theme.css roles: led, led-ready, led-partial, led-short, led-na)."""
    role = "led " + {
      "ready":   "led-ready",
      "partial": "led-partial",
      "short":   "led-short",
    }.get((state or "").lower(), "led-na")
    # Reset then apply (avoids class accumulation)
    self.label_materials_led.role = ""
    self.label_materials_led.role = role

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
    Finish:
      - Consumes external materials mapped to this op (using reservations if present,
        otherwise immediate reserve+consume)
      - Auto-transfers WIP to next cell bin, or produces FG if last step
      - Invalidates WOBOM cache so downstream rows recalc readiness
    """
    row = dict(self.item or {})
    try:
      anvil.server.call("tasks_complete", row.get("_id"))
      Notification("Finished.", timeout=2).show()
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







