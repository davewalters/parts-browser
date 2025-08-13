# client_code/SalesOrderLineRow/__init__.py
from ._anvil_designer import SalesOrderLineRowTemplate
from anvil import *
import anvil.server

class SalesOrderLineRow(SalesOrderLineRowTemplate):
  def __init__(self, parent_form=None, **props):
    self.init_components(**props)
    self.parent_form = parent_form
    self._apply_editability()

  def _apply_editability(self):
    editable = bool(self.parent_form and self.parent_form.order and self.parent_form.order.get("status") == "draft")
    # Only allow delete in draft; all fields displayed as Labels on the form
    self.button_delete.enabled = editable

  def button_delete_click(self, **event_args):
    try:
      anvil.server.call("delete_sales_order_line", self.item["_id"])
      self.parent_form._load()
    except Exception as ex:
      Notification(f"Delete failed: {ex}", style="warning").show()

