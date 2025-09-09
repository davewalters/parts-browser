from anvil import *

class CellRecordsRow(CellRecordsRowTemplate):
  """
  Summary row with two actions:
    - Details (edit in CellRecord)
    - Open (operator view in CellDetail)
  """
  def __init__(self, **properties):
    self.init_components(**properties)

  def form_show(self, **event_args):
    c = self.item or {}
    self.label_cell_id.text = c.get("_id", "—")
    self.label_cell_name.text = c.get("name", "—")
    self.label_cell_type.text = c.get("type", "—")
    self.label_active.text = "Active" if c.get("active", True) else "—"
    self.label_parallel_capacity.text = str(int(c.get("parallel_capacity", 1)))
    try:
      self.label_minute_cost_nz.text = f"${float(c.get('minute_cost_nz', 0.0)):.2f}/min"
    except Exception:
      self.label_minute_cost_nz.text = "—"
    self.label_wip_bin.text = c.get("default_wip_bin_id", "—")

  def button_details_click(self, **event_args):
    self.parent.raise_event("x-show-detail", row=self.item)

  def button_open_click(self, **event_args):
    self.parent.raise_event("x-show-operator", row=self.item)

