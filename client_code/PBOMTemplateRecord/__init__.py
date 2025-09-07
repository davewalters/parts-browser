from anvil import *
import anvil.server

class PBOMTemplateRecord(PBOMTemplateRecordTemplate):
  def __init__(self, pbom_id: str, **kwargs):
    self.init_components(**kwargs)
    self.pbom_id = pbom_id
    self._load()

  def _load(self):
    d = anvil.server.call("pbomtpl_get", self.pbom_id) or {}
    self.doc = d

    # Header labels
    self.label_id.text          = d.get("_id", "")
    self.label_parent_id.text   = d.get("parent_part_id", "")
    self.label_parent_desc.text = d.get("parent_desc", "") or ""
    self.label_status.text      = d.get("status", "draft")

    current = self.label_status.text
    allowed_map = {
      "draft":   ["draft", "active"],
      "active":  ["active", "obsolete"],
      "obsolete":["obsolete", "archived"],
      "archived":["archived"],
    }
    items = allowed_map.get(current, [current])
    self.drop_down_status.items = items
    self.drop_down_status.selected_value = current
    is_draft = (current == "draft")
    for c in [self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    # Header text boxes / area
    self.text_rev.text     = d.get("rev") or ""
    self.text_plant.text   = d.get("plant_id") or ""
    self.text_variant.text = d.get("variant") or ""
    self.text_notes.text   = d.get("notes") or ""

    is_draft = (self.label_status.text == "draft")

    # Enable header fields only in draft
    for c in [self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft


    # Lines
    self.repeating_panel_lines.items = d.get("lines", [])

  # ---- Header update-on-change ----
  def _save_header(self, patch: dict):
    if not patch:
      return
    if self.label_status.text != "draft":
      Notification("Header is read-only (status != draft)").show()
      return
    try:
      self.doc = anvil.server.call("pbomtpl_update", self.pbom_id, patch)
      self._load()
    except Exception as e:
      alert(f"Save failed: {e}")

  def drop_down_status_change(self, **e):
    old = self.label_status.text
    new = self.drop_down_status.selected_value or old
    if new == old:
      return
    try:
      # change on server; service enforces invalid transitions defensively
      updated = anvil.server.call("pbomtpl_set_status", self.pbom_id, new)
      if not updated:
        Notification("Transition not permitted").show()
        # reset dropdown to old value
        self.drop_down_status.selected_value = old
        return
      self._load()
    except Exception as ex:
      alert(f"Failed to change status: {ex}")
      self.drop_down_status.selected_value = old

  def text_rev_change(self, **e):
    self._save_header({"rev": self.text_rev.text or None})

  def text_plant_change(self, **e):
    self._save_header({"plant_id": self.text_plant.text or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": self.text_variant.text or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": self.text_notes.text or None})

  # ---- Status transitions ----
  def button_revise_click(self, **e):
    current_rev = self.text_rev.text or self.doc.get("rev") or ""
    dlg = PBOMReviseDialog(current_rev=current_rev)
    res = alert(dlg, title="Revise PBOM", buttons=[("Create", "OK"), ("Cancel", "CANCEL")])
    if res != "OK":
      return
    new_rev = (dlg.text_new_rev.text or "").strip()
    if not new_rev:
      Notification("Revision cannot be empty").show(); return
    try:
      clone = anvil.server.call("pbomtpl_revise_from", self.pbom_id, new_rev)
      if clone:
        open_form("PBOMTemplateRecord", pbom_id=clone["_id"])
    except Exception as ex:
      alert(f"Failed to create revision: {ex}")

