from anvil import *

def _norm_status(s: str) -> str:
  s = (s or "").lower().strip()
  if s in ("done", "complete", "completed", "finished"): return "done"
  if s in ("in_progress", "running"): return "in_progress"
  if s in ("queued", "waiting", "ready"): return "queued"
  if s in ("pause", "paused"): return "paused"
  return s or "queued"

class CellDetailRowTask(CellDetailRowTaskTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def form_show(self, **event_args):
    t = self.item or {}
    self.label_wo_id.text = t.get("wo_id")
    self.label_op_name.text = t.get("_op_name", f"OP{t.get('operation_seq')}")
    self.label_qty.text = f"Qty {t.get('qty')}"
    self.label_batch_runtime.text = f"Batch run-time: {t.get('batch_run_time_min') or '?'} min"
    #self.label_batch_runtime.tooltip = "Estimated minutes for the whole batch at this cell"

    self.label_next_cell.text = f"Next cell: {t.get('_next_cell_id','-')}"
    self.label_next_bin.text  = f"Next bin: {t.get('_next_bin_id','-')}"

    self.label_priority.text = f"Priority: {t.get('_bucket_label','')}"
    #self.label_priority.tooltip = "Overdue = do first • Today = do today • Upcoming = can wait"
    colors = {"Overdue": "#e74c3c", "Today": "#2ecc71", "Upcoming": "#3498db"}
    self.label_priority.foreground = colors.get(t.get('_bucket_label'), "#666")

    self.label_scheduled_date.text = f"Scheduled: {t.get('_scheduled_str','—')}"

    st = _norm_status(t.get("status"))
    self.label_status.text = st.replace("_", " ").title()

    is_queued  = (st == "queued")
    is_running = (st == "in_progress")
    is_paused  = (st == "paused")
    is_done    = (st == "done")

    self.button_start.text  = "Start"     # doubles as Resume
    self.button_pause.text  = "Pause"
    self.button_finish.text = "Finish"

    self.button_start.visible  = (is_queued or is_paused) and not is_done
    self.button_pause.visible  = is_running
    self.button_finish.visible = (is_running or is_paused) and not is_done

  def button_start_click(self, **event_args):
    self.parent.parent.task_start_or_resume_click(self.item)

  def button_pause_click(self, **event_args):
    self.parent.parent.task_pause_click(self.item)

  def button_finish_click(self, **event_args):
    self.parent.parent.task_finish_click(self.item)



