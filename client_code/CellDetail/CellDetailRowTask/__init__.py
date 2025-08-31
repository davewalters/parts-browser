from anvil import *

class CellDetailRowTask(CellDetailRowTaskTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def form_show(self, **event_args):
    t = self.item or {}
    self.lbl_wo_id.text = t.get("wo_id")
    self.lbl_op.text = t.get("_op_name", f"OP{t.get('operation_seq')}")
    self.lbl_qty.text = f"Qty {t.get('qty')}"
    self.lbl_batch_runtime.text = f"Batch run-time: {t.get('batch_run_time_min') or '?'} min"
  
    sd = t.get("scheduled_date")
    self.lbl_scheduled_date.text = f"Scheduled: {sd.isoformat() if sd else '—'}"
  
    bucket = t.get("_bucket", "")
    # Simple clear wording for operators
    bucket_label = {"overdue": "Overdue", "today": "Today", "upcoming": "Upcoming"}.get(bucket, "")
    self.lbl_bucket.text = bucket_label
    # Optional colour cue
    self.lbl_bucket.foreground = {"overdue": "#e74c3c", "today": "#2ecc71", "upcoming": "#3498db"}.get(bucket, "#666")
  
    st = t.get("status","queued")
    self.lbl_status.text = st.title()
  
    self.btn_start.visible = (st == "queued")
    self.btn_complete.visible = (st in ("queued", "in_progress"))


  def btn_start_click(self, **event_args):
    self.parent.parent.task_start_click(self.item)

  def btn_complete_click(self, **event_args):
    self.parent.parent.task_complete_click(self.item)

