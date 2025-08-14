# client_code/SalesOrderRecordsRow/__init__.py
from ._anvil_designer import SalesOrderRecordsRowTemplate
from anvil import *
from datetime import datetime, date

class SalesOrderRecordsRow(SalesOrderRecordsRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)
    self._bind()

  def _fmt_date(self, d):
    if isinstance(d, (date, datetime)):
      return d.strftime("%Y-%m-%d")
    try:
      return datetime.fromisoformat(d).strftime("%Y-%m-%d")
    except Exception:
      return str(d) if d else ""

  def _bind(self):
    so = self.item or {}
    self.label_so_id.text = so.get("_id","")
    self.label_customer_id.text = so.get("customer_id","")
    self.label_customer_name.text = so.get("customer_name","")
    self.label_order_date.text = self._fmt_date(so.get("order_date"))
    self.label_status.text = (so.get("status","") or "").upper()

    a = so.get("amounts", {}) or {}
    self.label_grand_total.text = f"{float(a.get('grand_total', 0.0) or 0.0):.2f}"

  def button_details_click(self, **e):
    open_form("SalesOrderRecord", order_id=self.item["_id"])

