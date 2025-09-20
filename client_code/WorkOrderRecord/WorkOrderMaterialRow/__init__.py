# client_code/WorkOrderMaterialRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderMaterialRowTemplate

class WorkOrderMaterialRow(WorkOrderMaterialRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)

  def form_show(self, **e):
    it = dict(self.item or {})
    self._doc = dict(it.get("_doc") or {})
  
    self.label_part_id.text = it.get("part_id","")
    self.label_desc.text = it.get("desc","")
    self.label_unit.text = it.get("unit","")
    self.text_qty_required.text = str(it.get("qty_required",0.0))
  
    # PBOM baseline label (grey)
    pb = it.get("pbom_qty", None)
    self.label_pbom_qty.text = "" if (pb is None) else f"PBOM: {pb:g}"
    self.label_pbom_qty.role = "muted"
  
    # Manual tag
    self.label_is_manual.text = "manual" if bool(it.get("is_manual")) else ""
  
    # NEW: step/cell info (grey)
    seq = it.get("issue_seq", None)
    cell = it.get("issue_cell_name", "")
    if seq is not None:
      self.label_step_info.text = f"Step {seq} · {cell}".strip()
    else:
      self.label_step_info.text = ""
  
    self.text_qty_required.set_event_handler('pressed_enter', self._save_qty)
    self.text_qty_required.set_event_handler('change', self._save_qty)


  def _save_qty(self, **e):
    try:
      v = float(self.text_qty_required.text)
      if v < 0:
        Notification("Qty must be >= 0").show(); return
      new_doc = dict(self._doc)
      new_doc["qty_required"] = v
      anvil.server.call("wobom_replace_line", new_doc)
      # Notify parent to refresh if it cares
      try:
        self.parent.raise_event("x-row-changed")
      except Exception:
        pass
    except Exception as ex:
      alert(f"Save failed: {ex}")

