# client_code/WorkOrderRouteRow/__init__.py
from anvil import *
from ._anvil_designer import WorkOrderRouteRowTemplate

class WorkOrderRouteRow(WorkOrderRouteRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)

  def form_show(self, **e):
    r = dict(self.item or {})
    self.label_seq.text = str(r.get("seq",""))
    self.label_cell_name.text = r.get("cell_name","")
    self.label_operation_name.text = r.get("operation_name","")
    self.label_cycle_min_per_unit.text = str(r.get("cycle_min_per_unit",""))

