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

    # labels
    self.label_id.text = d.get("_id", "")
    self.label_parent_id.text = d.get("parent_part_id", "")
    self.label_parent_desc.text = d.get("parent_desc", "")
    self.label_status.text = d.get("status", "draft")

    # text boxes
    self.text_rev.text = d.get("rev") or ""
    self.text_plant.text = d.get("plant_id") or ""
    self.text_variant.text = d.get("variant") or ""
    self.text_notes.text = d.get("notes") or ""

    is_draft = (self.label_status.text == "draft")

    # enable/disable header fields in draft only
    for c in [self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    # status buttons (names not mandated, left as-is)
    self.button_activate.enabled = (self.label_status.text == "draft")
    self.button_obsolete.enabled = (self.label_status.text == "active")
    self.button_archive.enabled  = (self.label_status.text == "obsolete")
    self.button_revise.enabled   = True

    # lines
    self.repeating_panel_lines.items = d.get("lines", [])

  # ---------- header auto-save (update-on-change) ----------
  def _save_header(self, patch: dict):
    if not patch:
      return
    if self.label_status.text != "draft":
      Notification("Header is read-only (status != draft)").show()
      return
    self.doc = anvil.server.call("pbomtpl_update", self.pbom_id, patch)
    self._load()

  def text_rev_change(self, **e):
    self._save_header({"rev": self.text_rev.text or None})

  def text_plant_change(self, **e):
    self._save_header({"plant_id": self.text_plant.text or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": self.text_variant.text or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": self.text_notes.text or None})

  # ---------- status transitions ----------
  def button_activate_click(self, **e):
    anvil.server.call("pbomtpl_set_status", self.pbom_id, "active")
    self._load()

  def button_obsolete_click(self, **e):
    anvil.server.call("pbomtpl_set_status", self.pbom_id, "obsolete")
    self._load()

  def button_archive_click(self, **e):
    anvil.server.call("pbomtpl_set_status", self.pbom_id, "archived")
    self._load()

  def button_revise_click(self, **e):
    res = alert(TextBox(text="B"), title="New revision", buttons=["OK","Cancel"])
    if res != "OK":
      return
    new_rev = get_open_form().content.text.strip()
    clone = anvil.server.call("pbomtpl_revise_from", self.pbom_id, new_rev)
    if clone:
      open_form("PBOMTemplateRecord", pbom_id=clone["_id"])

