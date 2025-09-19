from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderRowTemplate

class WorkOrderRow(WorkOrderRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)
    self.button_open.role = "mydefault-button"
    self.button_delete.role = "delete-button"

  def form_show(self, **event_args):
    r = self.item or {}
    self.label_work_order_id.text = r.get("_id", "")
    self.label_status.text = r.get("status", "")
    self.label_sales_order_id.text = r.get("sales_order_id", "")
    self.label_part_id.text = r.get("part_id", "")
    self.label_qty.text = str(r.get("qty", ""))
    self.label_due_date.text = str(r.get("due_date", ""))


  def button_open_click(self, **e):
    self.parent.raise_event("x-open-wo", wo_id=self.label_wo_id.text)

  def button_delete_click(self, **e):
    work_order_id = self.label_work_order_id.text
    if not confirm(f"Delete work order {work_order_id}? This will remove its materials."):
      return
    try:
      anvil.server.call("wo_delete", work_order_id)
      Notification("Deleted.", style="info").show()
      self.parent.raise_event("x-refresh")
    except Exception as ex:
      alert(f"Delete failed: {ex}")
