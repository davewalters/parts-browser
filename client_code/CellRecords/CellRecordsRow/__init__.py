# client_code/CellRecordsRow/__init__.py
from ._anvil_designer import CellRecordsRowTemplate
from anvil import *

class CellRecordsRow(CellRecordsRowTemplate):
  """
  Summary row with two actions:
    - Details (edit in CellRecord)
    - Open (operator view in CellDetail)
  Expects self.item to be a dict with keys:
    _id, name, type, active, parallel_capacity, minute_cost_nz, default_wip_bin_id
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    # Ensure our binder is called in both cases
    self.set_event_handler("refreshing_data_bindings", self._bind)
    self.set_event_handler("show", self._bind)  # 'form_show' alias

  def _bind(self, **event_args):
    c = self.item or {}
    try:
      # If there’s genuinely no item, clear labels
      if not c:
        self.label_cell_id.text = self.label_cell_name.text = self.label_cell_type.text = "—"
        self.label_active.text = "—"
        self.label_parallel_capacity.text = "—"
        self.label_minute_cost_nz.text = "—"
        self.label_wip_bin.text = "—"
        return

      self.label_cell_id.text           = c.get("_id", "—")
      self.label_cell_name.text         = c.get("name", "—")
      self.label_cell_type.text         = c.get("type", "—")
      self.label_active.text            = "Active" if c.get("active", True) else "—"
      self.label_parallel_capacity.text = str(int(c.get("parallel_capacity", 1)))
      try:
        self.label_minute_cost_nz.text  = f"${float(c.get('minute_cost_nz', 0.0)):.2f}/min"
      except Exception:
        self.label_minute_cost_nz.text  = "—"
      self.label_wip_bin.text           = c.get("default_wip_bin_id", "—")
    except Exception as e:
      # Failsafe: surface any unexpected template/component naming mismatch
      # (Comment out if you don't want UI alerts)
      Notification(f"Row bind error: {e}", style="danger", timeout=3).show()

  def button_details_click(self, **event_args):
    self.parent.raise_event("x-show-detail", row=self.item)

  def button_open_click(self, **event_args):
    self.parent.raise_event("x-show-operator", row=self.item)



