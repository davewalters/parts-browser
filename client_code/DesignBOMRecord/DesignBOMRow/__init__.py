from ._anvil_designer import DesignBOMRowTemplate
from anvil import *
import anvil.server

class DesignBOMRow(DesignBOMRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_delete_row.role = "delete-button"

  def form_show(self, **event_args):
    self.text_box_part_id.text = self.item.get('part_id', '')
    self.text_box_qty.text = str(self.item.get('qty', ''))
    self.update_description()

  def update_description(self):
    part_id = self.text_box_part_id.text.strip()
    print("update_description called")
    print(part_id)
    if not part_id:
      self.label_desc.text = ""
      self.label_status.text = ""
      self.label_unit.text = ""
      self.text_box_part_id.role = ""
      return

    part = anvil.server.call('get_part', part_id)
    if part:
      self.label_desc.text = part.get('description', "")
      self.label_status.text = part.get('status', "")
      self.label_unit.text = part.get('unit_of_issue', "")
      self.text_box_part_id.role = ""
    else:
      self.label_desc.text = "Part not found"
      self.label_status.text = ""
      self.label_unit.text = ""
      self.text_box_part_id.role = "input-error"

  def text_box_part_id_change(self, **event_args):
    self.item['part_id'] = self.text_box_part_id.text.strip()
    if len(self.item['part_id']) >= 3:
      self.update_description()

  def text_box_part_id_lost_focus(self, **event_args):
    self.item['part_id'] = self.text_box_part_id.text.strip()
    self.update_description()

  def text_box_qty_lost_focus(self, **event_args):
    try:
      self.item['qty'] = float(self.text_box_qty.text)
    except ValueError:
      self.item['qty'] = 0

  def button_delete_row_click(self, **event_args):
    self.parent.raise_event("x-delete-row", row=self)



