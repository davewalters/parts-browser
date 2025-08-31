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

    # New: explicit next destination (or "-")
    self.lbl_next_cell.text = f"Next cell: {t.get('_next_cell_id','-')}"
    self.lbl_next_bin.text  = f"Next bin: {t.get('_next_bin_id','-')}"

    st = t.get("status","queued")
    self.lbl_status.text = st.title()

    self.btn_start.text = "Start"
    self.btn_complete.text = "Finish"
    self.btn_start.visible = (st == "queued")
    self.btn_complete.visible = (st in ("queued", "in_progress"))

  def btn_start_click(self, **event_args):
    self.parent.parent.task_start_click(self.item)

  def btn_complete_click(self, **event_args):
    self.parent.parent.task_complete_click(self.item)

