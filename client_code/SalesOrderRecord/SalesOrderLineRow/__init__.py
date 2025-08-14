from ._anvil_designer import SalesOrderLineRowTemplate
from anvil import *
from datetime import datetime, date

class SalesOrderLineRow(SalesOrderLineRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)
    self._bind()

  def _fmt(self, x):
    try:
      return f"{float(x or 0.0):.2f}"
    except Exception:
      return "0.00"

  def _fmt_date(self, d):
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
      if isinstance(d, str):
        return d.split("T")[0]
    except Exception:
      pass
    return ""

  def _bind(self):
    line = self.item or {}
    # Expecting keys from server: part_id, description, uom, qty_ordered, unit_price, line_tax, line_total (if you compute it)
    self.label_line_no.text   = str(line.get("line_no",""))
    self.label_part_id.text   = line.get("part_id","")
    self.label_desc.text      = line.get("description","")
    self.label_uom.text       = line.get("uom","ea")
    self.label_qty.text       = self._fmt(line.get("qty_ordered", 0))
    self.label_unit_price.text= self._fmt(line.get("unit_price", 0))
    self.label_line_tax.text  = self._fmt(line.get("line_tax", 0))
    # If your server provides per-line total:
    if hasattr(self, "label_line_total"):
      self.label_line_total.text = self._fmt(line.get("line_total", (line.get("qty_ordered",0) or 0) * (line.get("unit_price",0) or 0)))


