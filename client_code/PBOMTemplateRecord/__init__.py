from anvil import *
import anvil.server
import re

class PBOMTemplateRecord(PBOMTemplateRecordTemplate):
  """
  Production BOM Template Record
  - Header fields auto-save on change when status == 'draft'
  - Status is controlled via drop_down_status (valid next states only)
  - Revision is controlled via drop_down_rev: [current_rev, next_rev]
      Selecting next_rev creates a new PBOM (revise_from) and opens it
  - Lines are edited via repeating_panel_lines (item_template: PBOMTemplateLineRow)
  """

  def __init__(self, pbom_id: str, **kwargs):
    self.init_components(**kwargs)
    self.pbom_id = pbom_id
    self.doc = {}
    self.repeating_panel_lines.role = "scrolling-panel"
    self.button_home.role = "mydefault-button"
    self.button_regenerate.role = "new-button"
    self._load()

  def _load(self):
    d = anvil.server.call("pbomtpl_get", self.pbom_id) or {}
    self.doc = d
    self.label_id.text          = d.get("_id", "")
    self.label_parent_id.text   = d.get("parent_part_id", "")
    self.label_parent_desc.text = d.get("parent_desc", "") or ""
    status = d.get("status", "draft")

    rev = d.get("rev") or ""
    self.text_plant.text   = d.get("plant_id") or ""
    self.text_variant.text = d.get("variant") or ""
    self.text_notes.text   = d.get("notes") or ""

    is_draft = (status == "draft")
    self.button_regenerate.visible  = True
    self.button_regenerate.enabled  = is_draft
    for c in [self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    self._bind_status_dropdown(status)
    is_archived = (status == "archived")
    self._bind_rev_dropdown(rev, is_archived)
    self.repeating_panel_lines.items = d.get("lines", [])
    


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

  def text_plant_change(self, **e):
    self._save_header({"plant_id": self.text_plant.text or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": self.text_variant.text or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": self.text_notes.text or None})

  def _bind_status_dropdown(self, current: str):
    """
    Transition matrix:
      draft    -> active
      active   -> obsolete
      obsolete -> archived
      archived -> (no further transitions)
    The dropdown shows only [current, next] (or just [current] if terminal).
    """
    allowed_map = {
      "draft":    ["draft", "active"],
      "active":   ["active", "obsolete"],
      "obsolete": ["obsolete", "archived"],
      "archived": ["archived"],
    }
    items = allowed_map.get(current, [current])
    self.drop_down_status.items = items
    self.drop_down_status.selected_value = current
    self.drop_down_status.enabled = (len(items) > 1)

  def drop_down_status_change(self, **e):
    old = self.label_status.text
    new = self.drop_down_status.selected_value or old
    if new == old:
      return
    try:
      updated = anvil.server.call("pbomtpl_set_status", self.pbom_id, new)
      if not updated:
        Notification("Transition not permitted").show()
        self.drop_down_status.selected_value = old
        return
      self._load()
    except Exception as ex:
      alert(f"Failed to change status: {ex}")
      self.drop_down_status.selected_value = old

  def _bind_rev_dropdown(self, current_rev: str, is_archived: bool):
    """
    Provide [current_rev, next_rev]. Selecting next_rev triggers revise_from.
    Disabled when archived.
    """
    next_rev = self._next_alpha_rev(current_rev or "")
    items = []
    if current_rev:
      items.append(current_rev)
    if next_rev and next_rev != current_rev:
      items.append(next_rev)

    # Fallback if no rev yet (brand new): offer "A"
    if not items:
      items = ["A"]

    self.drop_down_rev.items = items
    # Select current if present, else the first item
    self.drop_down_rev.selected_value = current_rev if current_rev in items else items[0]
    self.drop_down_rev.enabled = (not is_archived) and (len(items) > 1)

  def drop_down_rev_change(self, **e):
    """
    If operator selects the next revision, create a new PBOM via revise_from.
    If they re-select the current revision, do nothing.
    """
    current_rev = self.doc.get("rev") or ""
    selected_rev = self.drop_down_rev.selected_value or current_rev
    if selected_rev == current_rev:
      return  # retain

    try:
      # Server enforces (parent_part_id, new_rev) uniqueness and creates a draft clone
      clone = anvil.server.call("pbomtpl_revise_from", self.pbom_id, selected_rev)
      if clone:
        open_form("PBOMTemplateRecord", pbom_id=clone["_id"])
    except Exception as ex:
      alert(f"Failed to create revision: {ex}")
      # Snap UI back
      self.drop_down_rev.selected_value = current_rev

  def _next_alpha_rev(self, cur: str) -> str:
    """
    Alpha-based revision series:
      A -> B,  Z -> AA,  AA -> AB, ...
    If the current value ends with digits, increment the numeric suffix:
      A1 -> A2,  R01 -> R02
    If empty/unknown, return 'A'.
    """
    if not cur:
      return "A"

    if re.fullmatch(r"[A-Z]+", cur):
      chars = list(cur)
      i = len(chars) - 1
      carry = True
      while i >= 0 and carry:
        if chars[i] == 'Z':
          chars[i] = 'A'
          i -= 1
          carry = True
        else:
          chars[i] = chr(ord(chars[i]) + 1)
          carry = False
      return ("A" + "".join(chars)) if carry else "".join(chars)

    m = re.fullmatch(r"(.*?)(\d+)$", cur)
    if m:
      head, digits = m.groups()
      return f"{head}{int(digits)+1:0{len(digits)}d}"

    return cur + "A"

  def button_regenerate_click(self, **e):
    if self.label_status.text != "draft":
      Notification("Can only regenerate lines while in draft.").show()
      return
    if confirm("Rebuild lines from DesignBOM? This will replace current lines."):
      anvil.server.call("pbomtpl_regenerate_from_design", self.pbom_id)
      self._load()


