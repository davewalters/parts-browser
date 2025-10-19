from ._anvil_designer import PBOMTemplateListRowTemplate
from anvil import *

class PBOMTemplateListRow(PBOMTemplateListRowTemplate):
  def __init__(self, **kwargs):
    # IMPORTANT: __init__ receives 'item' via **kwargs from the RepeatingPanel.
    self.init_components(**kwargs)

    # Remove any designer bindings that might conflict
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
        w.data_bindings = []
      except Exception:
        pass

    # Render immediately from the initial item (mirrors your CustomerRecordsRow pattern)
    self._render(self.item or kwargs.get("item") or {})

  # RepeatingPanel calls this whenever it (re)assigns the row's item
  def set_item(self, item):
    self.item = item or {}
    self._render(self.item)

  def _render(self, i):
    self.label_id.text          = (i.get("display_id") or i.get("id") or i.get("_id") or "")
    self.label_parent_id.text   = i.get("parent_part_id") or ""
    self.label_parent_desc.text = i.get("parent_desc") or ""
    self.label_rev.text         = i.get("rev") or ""
    self.label_plant.text       = i.get("plant_id") or ""
    self.label_variant.text     = i.get("variant") or ""
    self.label_status.text      = i.get("status") or ""
 
  def button_select_click(self, **event_args):
    open_form("PBOMTemplateRecord",
              pbom_id=self.item.get("display_id"),
              parent_prefix="",
              status="",
              rev="",
              plant="",
             )





