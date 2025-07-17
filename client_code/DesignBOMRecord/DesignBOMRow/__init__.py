from ._anvil_designer import DesignBOMRowTemplate
from anvil import *
import anvil.server

class DesignBOMRow(DesignBOMRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_remove_row.role = "delete-button"

  def form_show(self, **event_args):
    print("form_show triggered")
    self.text_box_part_id.text = self.item.get('part_id', '')
    self.text_box_qty.text = str(self.item.get('qty', ''))
    self.update_description()

  def update_description(self):
    part_id = self.text_box_part_id.text.strip()
    print(f"🔍 update_description for: {part_id}")

    if not part_id:
      self.label_desc.text = ""
      self.label_status.text = ""
      self.label_unit.text = ""
      self.text_box_part_id.role = ""
      self.item['is_valid_part'] = False
      self.parent.raise_event("x-validation-updated")
      print("no part_id - invalid part")
      return

    part = anvil.server.call('get_part', part_id)
    if part:
      self.label_desc.text = part.get('description', "")
      self.label_status.text = part.get('status', "")
      self.label_unit.text = part.get('unit', "")
      self.text_box_part_id.role = ""
      self.item['is_valid_part'] = True
    else:
      self.label_desc.text = "Part not found"
      self.label_status.text = ""
      self.label_unit.text = ""
      self.text_box_part_id.role = "input-error"
      self.item['is_valid_part'] = False
    print("part_id exists")
    print(self.item['is_valid_part'])
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
    self.raise_event("x-remove-row", row=self)





