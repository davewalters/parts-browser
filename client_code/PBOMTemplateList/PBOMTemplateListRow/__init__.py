from ._anvil_designer import PBOMTemplateListRowTemplate
from anvil import *

class PBOMTemplateListRow(PBOMTemplateListRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    # Remove any designer-set data bindings that could blank out our labels on refresh
    self._clear_bindings()

  # Belt-and-braces: render on both events
  def form_show(self, **event_args):
    self._render()

  def refreshing_data_bindings(self, **event_args):
    self._render()

  def _clear_bindings(self):
    # If your designer added bindings (common), they can override manual .text assignments.
    for w in [
      self.label_id,
      self.label_parent_id,
      self.label_parent_desc,
      self.label_rev,
      self.label_plant,
      self.label_variant,
      self.label_status,
    ]:
      try:
        w.data_bindings = []   # clears any Item['x'] bindings
      except Exception:
        pass

  def _render(self):
    i = self.item or {}

    # Prefer the human PBOM code if present; otherwise show the (string) _id
    pbom_code = (i.get("id") or i.get("_id") or "") or ""
    parent_id = (i.get("parent_part_id") or "") or ""
    parent_desc = (i.get("parent_desc") or "") or ""
    rev = (i.get("rev") or "") or ""
    plant = (i.get("plant_id") or "") or ""
    variant = (i.get("variant") or "") or ""
    status = (i.get("status") or "") or ""

    self.label_id.text = pbom_code
    self.label_parent_id.text = parent_id
    self.label_parent_desc.text = parent_desc
    self.label_rev.text = rev
    self.label_plant.text = plant
    self.label_variant.text = variant
    self.label_status.text = status

  def button_select_click(self, **event_args):
    # Bubble up to the list to handle navigation
    self.parent.raise_event("x-open-detail", row=self.item)




