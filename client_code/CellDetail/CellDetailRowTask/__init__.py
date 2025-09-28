from anvil import *
import anvil.server

class CellDetailRowTask(CellDetailRowTaskTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def form_show(self, **event_args):
    d = self.item or {}

    # Priority (first column)
    self.label_priority.text = str(d.get("priority", ""))

    # Standardized labels
    self.label_wo_id.text = d.get("wo_id", "—")
    self.label_op_name.text = f"OP{d.get('operation_seq')}" if d.get("operation_seq") else "—"
    self.label_qty.text = str(d.get("qty", ""))
    self.label_status.text = (d.get("status") or "").replace("_", " ").title()
    self.label_scheduled_date.text = d.get("_scheduled_str", "—")
    self.label_next_cell.text = d.get("_next_cell_id", "-")
    self.label_next_bin.text = d.get("_next_bin_id", "-")

    brt = d.get("batch_run_time_min")
    self.label_batch_runtime.text = f"{brt:.1f} min" if isinstance(brt, (int, float)) else "—"

    # Material readiness pill (color + label)
    readiness = d.get("_mat_status") or "unknown"
    self.material_pill.role = {
      "ready": "success",
      "partial": "warning",
      "short": "danger"
    }.get(readiness, "default")
    self.material_pill.text = readiness.title()

  # ---- Actions bound to row buttons ----
  def button_start_click(self, **event_args):
    try:
      anvil.server.call('tasks_start', self.item["_id"])
      self.parent.raise_event('x-refresh')
    except Exception as e:
      Notification(f"Start failed: {e}", style="danger").show()

  def button_pause_click(self, **event_args):
    try:
      anvil.server.call('tasks_pause', self.item["_id"])
      self.parent.raise_event('x-refresh')
    except Exception as e:
      Notification(f"Pause failed: {e}", style="danger").show()

  def button_resume_click(self, **event_args):
    try:
      anvil.server.call('tasks_resume', self.item["_id"])
      self.parent.raise_event('x-refresh')
    except Exception as e:
      Notification(f"Resume failed: {e}", style="danger").show()

  def button_finish_click(self, **event_args):
    try:
      anvil.server.call('tasks_complete', self.item["_id"])
      self.parent.raise_event('x-refresh')
    except Exception as e:
      Notification(f"Finish failed: {e}", style="danger").show()

  def button_pick_click(self, **event_args):
    """Generate reservations & picklist for this WO."""
    try:
      anvil.server.call('flow_generate_picklist_by_destination', self.item["wo_id"])
      Notification("Picklist generated.", timeout=3).show()
      self.parent.raise_event('x-refresh')
    except Exception as e:
      Notification(f"Pick failed: {e}", style="danger").show()





