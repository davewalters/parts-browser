# client_code/PicklistRecordsRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PicklistRecordsRowTemplate

class PicklistRecordsRow(PicklistRecordsRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_open.role = "mydefault-button"

  def form_show(self, **event_args):
    d = dict(self.item or {})
    self.label_picklist_id.text = d.get("_id","")
    self.label_wo_id.text = d.get("wo_id","")
    self.label_sales_order_id.text = d.get("sales_order_id","") or ""
    self.label_status.text = d.get("status","") or d.get("_view_status","")
    self.label_created_ts.text = str(d.get("created_ts",""))
    self.label_mode.text = d.get("mode","")
    # Summarize all destination bins on this picklist (unique)
    bins = sorted({ (ln.get("to_bin") or "") for ln in (d.get("lines") or []) if ln.get("to_bin") })
    self.label_dest_bins.text = ", ".join(bins)

  def button_open_click(self, **event_args):
    d = dict(self.item or {})
    self.parent.raise_event("x-open", picklist_id=d.get("_id"))

