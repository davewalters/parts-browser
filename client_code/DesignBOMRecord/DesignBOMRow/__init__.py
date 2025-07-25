from ._anvil_designer import DesignBOMRowTemplate
from anvil import *
import anvil.server

class DesignBOMRow(DesignBOMRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_remove_row.role = "delete-button"
    self.button_edit_vendor.role = "mydefault-button"
    self.label_cost_nz.visible = True

  def form_show(self, **event_args):
    self.text_box_part_id.text = self.item.get('part_id', '')
    self.text_box_qty.text = str(self.item.get('qty', ''))
    self.update_description()

  def update_description(self):
    part_id = self.text_box_part_id.text.strip()
    if not part_id:
      self.label_desc.text = ""
      self.label_status.text = ""
      self.label_unit.text = ""
      self.label_cost_nz.text = ""
      self.text_box_part_id.role = ""
      self.item['is_valid_part'] = False
      self.parent.raise_event("x-validation-updated")
      return

    # Try to get cached part from parent
    parent = self.parent
    part_cache = getattr(parent, "part_cache", {})
    if part_id in part_cache:
      part = part_cache[part_id]
    else:
      part = anvil.server.call("get_part", part_id)
      if isinstance(part_cache, dict):  # Safety
        part_cache[part_id] = part
      if hasattr(parent, "part_cache"):
        parent.part_cache = part_cache
  
    if part:
      self.label_desc.text = part.get('description', "")
      self.label_status.text = part.get('status', "")
      self.label_unit.text = part.get('unit', "")
      latest_cost = part.get("latest_cost", {})
      cost_nz = latest_cost.get("cost_nz", "")
      self.label_cost_nz.text = self.format_currency(cost_nz)
      self.item['is_valid_part'] = True
      self.text_box_part_id.role = ""
    else:
      self.label_desc.text = "Part not found"
      self.label_status.text = ""
      self.label_unit.text = ""
      self.label_cost_nz.text = "–"
      self.text_box_part_id.role = "input-error"
      self.item['is_valid_part'] = False
  
    self.parent.raise_event("x-validation-updated")


  def text_box_part_id_change(self, **event_args):
    self.item['part_id'] = self.text_box_part_id.text.strip()
    if len(self.item['part_id']) >= 3:
      self.update_description()

  def text_box_part_id_lost_focus(self, **event_args):
    self.item['part_id'] = self.text_box_part_id.text.strip()
    self.update_description()

  def text_box_qty_change(self, **event_args):
    try:
      self.item['qty'] = float(self.text_box_qty.text.strip())
    except ValueError:
      self.item['qty'] = 0

  def text_box_qty_lost_focus(self, **event_args):
    try:
      self.item['qty'] = float(self.text_box_qty.text.strip())
    except ValueError:
      self.item['qty'] = 0

  def button_remove_row_click(self, **event_args):
    self.parent.raise_event("x-remove-row", row=self)

  def button_edit_vendor_click(self, **event_args):
    part_id = self.item.get("part_id")
    if part_id:
      self.parent.raise_event("x-edit-vendor", part_id=part_id)

  def format_currency(self, value):
    """Format a float as NZ currency, or return '–' if invalid."""
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"









