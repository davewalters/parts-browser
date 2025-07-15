from anvil import *
import anvil.server
from ._anvil_designer import DesignBOMRecordTemplate
import anvil.http
import json
from datetime import datetime
from . import DesignBOMRecordRow
from .. import config

class DesignBOMRecord(DesignBOMRecordTemplate):
  def __init__(self, assembly_part_id, **properties):
    self.init_components(**properties)
    self.assembly_part_id = assembly_part_id
    self.bom_rows = []
    self.button_add_row.role = "new-button"
    self.button_save.role = "save-button"

    self.label_assembly_id.text = self.assembly_part_id
    self.load_existing_bom()

  def load_existing_bom(self):
    bom_doc = anvil.server.call('get_design_bom', self.assembly_part_id)
    self.bom_rows = []
    for comp in bom_doc.get("components", []):
      row = DesignBOMRecordRow(part_id=comp["part_id"], qty=comp["qty"], parent_form=self)
      self.bom_rows.append(row)
    self.repeating_panel_1.items = self.bom_rows
    self.cost_status_label.text = ""

  def button_add_row_click(self, **event_args):
    row = DesignBOMRecordRow(part_id="", qty=1, parent_form=self)
    self.bom_rows.append(row)
    self.repeating_panel_1.items = self.bom_rows

  def button_save_click(self, **event_args):
    self.label_cost_status.text = "Saving and rolling up costs..."
    self.rollup_spinner.visible = True
    self.button_save.enabled = False
  
    try:
      components = self.collect_components()
      result = anvil.server.call('save_design_bom', self.assembly_part_id, components)
  
      cost = result['cost_nz']
      skipped = result['skipped_parts']
      updated = result['updated_assemblies']
  
      msg = f"Cost updated: ${cost:.2f}"
      if skipped:
        msg += f" — {len(skipped)} parts skipped (inactive or missing)"
      self.cost_status_label.text = msg
    except Exception as e:
      self.cost_status_label.text = f"Error: {str(e)}"
    finally:
      self.rollup_spinner.visible = False
      self.button_save.enabled = True
    
  def collect_components(self):
    components = []
    for row in self.bom_rows:
      if not row.part_id_input.text or not row.qty_input.text:
        continue
      try:
        qty = float(row.qty_input.text)
      except ValueError:
        raise Exception(f"Invalid quantity: {row.qty_input.text}")
      components.append({"part_id": row.part_id_input.text.strip(), "qty": qty})
    return components
    
  def remove_row(self, row):
    self.bom_rows.remove(row)
    self.repeating_panel_1.items = self.bom_rows
