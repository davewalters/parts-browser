from anvil import *
import anvil.server

from ._anvil_designer import DesignBOMRecordTemplate
from datetime import datetime
from .. import config
from .DesignBOMRow import DesignBOMRow

class DesignBOMRecord(DesignBOMRecordTemplate):
  def __init__(self, assembly_part_id, **properties):
    self.init_components(**properties)
    self.assembly_part_id = assembly_part_id
    self.button_add_row.role = "new-button"
    self.button_save_bom.role = "save-button"
    self.label_assembly_id.text = self.assembly_part_id
    self.timer_validate_rows.enabled = True
    self.repeating_panel_1.set_event_handler("x-validation-updated", self.validate_all_rows)
    self.repeating_panel_1.set_event_handler("x-remove-row", self.remove_row)
    self.load_existing_bom()

    # Set up a timer to poll for status
    self.timer_status_poll.interval = 0.5
    self.timer_status_poll.enabled = False
    #self.spinner_rollup.visible = False

  def load_existing_bom(self):
    self.button_save_bom.enabled = False
    bom_doc = anvil.server.call('get_design_bom', self.assembly_part_id)
    self.bom_rows = bom_doc.get("components", [])
    self.repeating_panel_1.items = self.bom_rows
    self.label_cost_status.text = ""

  def validate_all_rows(self, **event_args):
    validities = []
    for row in self.repeating_panel_1.get_components():
      valid = row.item.get("is_valid_part", False)
      print(f"🧪 Validating row: {row.item.get('part_id')} → is_valid_part={valid}")
      validities.append(valid)

    all_valid = all(validities)
    print(f"✅ All rows valid: {all_valid}")
    self.button_save_bom.enabled = all_valid


  def button_add_row_click(self, **event_args):
    updated_bom = []
    for row in self.repeating_panel_1.get_components():
      updated_bom.append({
        "part_id": row.text_box_part_id.text.strip(),
        "qty": float(row.text_box_qty.text.strip()) if row.text_box_qty.text.strip() else 0
      })
    updated_bom.append({"part_id": "", "qty": 1})
    self.bom_rows = updated_bom
    self.repeating_panel_1.items = self.bom_rows

  def button_save_bom_click(self, **event_args):
    print("🔘 Save button clicked")
    self.label_cost_status.text = "Saving and rolling up costs..."
    self.button_save_bom.enabled = False
    self.status_check_index = 0
    self.spinner_rollup.visible = True
    self.timer_status_poll.enabled = True

    try:
      print("🛰 Calling server: save_design_bom_with_progress_polling")
      result = anvil.server.call('save_design_bom_with_progress_polling',
                                 self.assembly_part_id,
                                 self.repeating_panel_1.items)
      print("✅ Server call returned")

      # ✅ Stop polling before final label update
      self.timer_status_poll.enabled = False
      self.spinner_rollup.visible = False

      cost = result["cost_nz"]
      skipped = result["skipped_parts"]
      msg = f"Cost updated: ${cost:.2f}"
      if skipped:
        msg += f" — {len(skipped)} parts skipped (inactive or missing)"
      self.label_cost_status.text = msg

    except Exception as e:
      self.label_cost_status.text = f"Error: {str(e)}"

    finally:
      self.button_save_bom.enabled = True

  def timer_status_poll_tick(self, **event_args):
    msg = anvil.server.call('get_rollup_status')
    if msg:
      self.label_cost_status.text = msg

  def timer_validate_rows_tick(self, **event_args):
    self.timer_validate_rows.enabled = False  # one-shot timer
    self.validate_all_rows()

  def remove_row(self, **event_args):
    row_to_remove = event_args['row']
    updated_bom = []
    for row in self.repeating_panel_1.get_components():
      if row is not row_to_remove:
        updated_bom.append({
          "part_id": row.text_box_part_id.text.strip(),
          "qty": float(row.text_box_qty.text.strip()) if row.text_box_qty.text.strip() else 0
        })
    self.bom_rows = updated_bom
    self.repeating_panel_1.items = self.bom_rows




