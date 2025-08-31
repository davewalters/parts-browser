from anvil import *

class CellDetailRowTask(CellDetailRowTaskTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def form_show(self, **event_args):
    t = self.item or {}
    self.label_wo_id.text = t.get("wo_id")
    self.label_op_name.text = t.get("_op_name", f"OP{t.get('operation_seq')}")
    self.label_qty.text = f"Qty {t.get('qty')}"
    self.label_batch_runtime.text = f"Batch run-time: {t.get('batch_run_time_min') or '?'} min"

    # New: explicit next destination
    self.label_next_cell.text = f"Next cell: {t.get('_next_cell_id','-')}"
    self.label_next_bin.text  = f"Next bin: {t.get('_next_bin_id','-')}"

    # New: bucket visibility as “Priority”
    self.label_priority.text = f"Priority: {t.get('_bucket_label','')}"
    # optional colour cue
    colors = {"Overdue": "#e74c3c", "Today": "#2ecc71", "Upcoming": "#3498db"}
    self.label_priority.foreground = colors.get(t.get('_bucket_label'), "#666")

    # New: dates
    self.label_scheduled_date.text = f"Scheduled: {t.get('_scheduled_str','—')}"
    #self.label_wo_due.text = f"WO due: {t.get('_wo_due_str','—')}"

    st = t.get("status","queued")
    self.label_status.text = st.title()

    #self.btn_start.text = "Start"
    #self.btn_finish.text = "Finish"
    self.button_start.visible = (st == "queued")
    self.button_finish.visible = (st in ("queued", "in_progress"))

  def button_start_click(self, **event_args):
    self.parent.parent.task_start_click(self.item)

  def button_finish_click(self, **event_args):
    self.parent.parent.task_finish_click(self.item)


