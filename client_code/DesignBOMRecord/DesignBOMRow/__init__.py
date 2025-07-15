from ._anvil_designer import DesignBOMRowTemplate
from anvil import *
import anvil.server

class DesignBOMRow(DesignBOMRowTemplate):
  def __init__(self, part_id, qty, parent_form, **properties):
    self.init_components(**properties)
    self.parent_form = parent_form
    self.button_delete_row.role = "delete-button"
    self.text_box_part_id.text = part_id
    self.text_box_qty.text = str(qty)
    self.update_description()

  def update_description(self):
    part = app_tables.parts.get(part_id=self.text_box_part_id.text.strip())
    if part:
      desc = part.get('description', "")
      unit = part.get('unit_of_issue', "")
      status = part.get('status', "")
      self.label_desc.text = desc
      self.label_status.text = status
      self.label_unit.text = unit
    else:
      self.label_desc.text = "Part not found"

  def part_id_input_lost_focus(self, **event_args):
    self.update_description()

  def button_delete_row_click(self, **event_args):
    self.parent_form.remove_row(self)
