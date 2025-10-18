
from anvil import *
import anvil.server
import re
from ._anvil_designer import PBOMTemplateRecordTemplate

class PBOMTemplateRecord(PBOMTemplateRecordTemplate):
  """
  Header:
    - parent_id: TextBox (text_parent_id)
    - status:    DropDown (drop_down_status)
    - rev:       DropDown (drop_down_rev)
    - plant:     TextBox (text_plant)
    - variant:   TextBox (text_variant)
    - notes:     TextArea (text_notes)

  Modes:
    - New (pbom_id is None): operator types parent_id, presses Enter; can pick initial rev
      via drop_down_rev (defaults to 'A'). Status is 'draft' and not changeable until saved.
    - Existing: loads doc; header auto-saves while status == 'draft'.
  """

  def __init__(self, pbom_id=None, parent_prefix="", status="", rev="", plant="", **kwargs):
    self.init_components(**kwargs)
    self.pbom_id = pbom_id if pbom_id else None
    self.doc = {}
    self._status = "draft"   # cached current status for guards
    self._rev = ""           # cached current rev

    # Roles
    self.repeating_panel_lines.role = "scrolling-panel"
    self.button_home.role = "mydefault-button"
    self.button_regenerate.role = "new-button"
    self.button_create.role = "save-button"

    # Events
    self.text_parent_id.set_event_handler("pressed_enter", self._resolve_parent_on_enter)
    self.text_plant.set_event_handler("change", self.text_plant_change)
    self.text_variant.set_event_handler("change", self.text_variant_change)
    self.text_notes.set_event_handler("change", self.text_notes_change)
    self.drop_down_status.set_event_handler("change", self.drop_down_status_change)
    self.drop_down_rev.set_event_handler("change", self.drop_down_rev_change)

    if self.pbom_id:
      self._load()
    else:
      self._init_new_blank(parent_prefix, status, rev, plant)

  # ---------- New-record (unsaved) mode ----------

  def _init_new_blank(self, parent_prefix, status, rev, plant):
    self.label_id.text = "(unsaved)"
    self.text_parent_id.text = ""       # operator enters
    self.label_parent_desc.text = ""
    self.text_plant.text = (plant or "").strip()
    self.text_variant.text = ""
    self.text_notes.text = ""
    self.repeating_panel_lines.items = []
    self.button_create.visible = True
    self.button_create.enabled = False
    self.button_regenerate.visible = False

    # Status dropdown: force 'draft', not changeable until saved
    self._status = "draft"
    self._bind_status_dropdown(self._status)
    self.drop_down_status.enabled = False

    # Rev dropdown: for a brand-new record with no current rev, offer ["A"] (or provided)
    self._rev = (rev or "").strip() or "A"
    self._bind_rev_dropdown(self._rev, is_archived=False)
    # Allow choosing initial rev before creation
    self.drop_down_rev.enabled = True

    # Enable header entry fields
    for c in [self.text_parent_id, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = True

  def _resolve_parent_on_enter(self, **e):
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      Notification("Enter a valid parent_id.").show()
      return
    try:
      part = anvil.server.call("get_part_brief", pid)
    except Exception as ex:
      alert(f"Lookup failed: {ex}")
      return

    if not part:
      self.label_parent_desc.text = ""
      self.button_create.enabled = False
      Notification("Parent not found.").show()
      return

    self.label_parent_desc.text = part.get("description") or part.get("part_name") or ""
    self.button_create.enabled = True

  def button_create_click(self, **e):
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      Notification("Enter a valid parent_id first.").show()
      return

    payload = {
      "parent_part_id": pid,
      "rev": (self.drop_down_rev.selected_value or "A"),
      "plant_id": (self.text_plant.text or None) or None,
      "variant": (self.text_variant.text or None) or None,
      "notes": (self.text_notes.text or None) or None,
    }
    try:
      created = anvil.server.call("pbomtpl_create_draft", payload)
    except Exception as ex:
      alert(f"Create failed: {ex}")
      return

    if not created:
      alert("Create failed (no document returned).")
      return

    open_form("PBOMTemplateRecord", pbom_id=created["_id"])

  # ---------- Existing-record mode ----------

  def _load(self):
    d = anvil.server.call("pbomtpl_get", self.pbom_id) or {}
    self.doc = d

    # Header bindings
    self.label_id.text          = d.get("_id", "")
    self.text_parent_id.text    = d.get("parent_part_id", "") or ""
    self.label_parent_desc.text = d.get("parent_desc", "") or ""
    self._status                = d.get("status", "draft")
    self._rev                   = d.get("rev") or ""
    self.text_plant.text        = d.get("plant_id") or ""
    self.text_variant.text      = d.get("variant") or ""
    self.text_notes.text        = d.get("notes") or ""

    is_draft = (self._status == "draft")
    for c in [self.text_parent_id, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    self.button_create.visible = False
    self.button_regenerate.visible = True
    self.button_regenerate.enabled = is_draft

    # Status & Rev dropdowns
    self._bind_status_dropdown(self._status)
    is_archived = (self._status == "archived")
    self._bind_rev_dropdown(self._rev, is_archived)

    # Lines
    self.repeating_panel_lines.items = d.get("lines", [])

  # ---------- Header autosave (existing + draft) ----------

  def _save_header(self, patch):
    if not patch or not self.pbom_id:
      return
    if self._status != "draft":
      Notification("Header is read-only (status ≠ draft).").show()
      return
    try:
      self.doc = anvil.server.call("pbomtpl_update", self.pbom_id, patch)
      self._load()
    except Exception as e:
      alert(f"Save failed: {e}")

  def text_parent_id_change(self, **e):
    if not self.pbom_id:
      return  # in new mode, we only resolve on Enter
    pid = (self.text_parent_id.text or "").strip()
    try:
      part = anvil.server.call("get_part_brief", pid) if pid else None
      self.label_parent_desc.text = (part or {}).get("description") or (part or {}).get("part_name") or ""
    except Exception:
      self.label_parent_desc.text = ""
    self._save_header({"parent_part_id": pid})

  def text_plant_change(self, **e):
    self._save_header({"plant_id": (self.text_plant.text or None) or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": (self.text_variant.text or None) or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": (self.text_notes.text or None) or None})

  # ---------- Status & Revision ----------

  def _bind_status_dropdown(self, current):
    # Transition matrix like original:
    #   draft -> active -> obsolete -> archived
    allowed_map = {
      "draft":    ["draft", "active"],
      "active":   ["active", "obsolete"],
      "obsolete": ["obsolete", "archived"],
      "archived": ["archived"],
    }
    items = allowed_map.get(current, [current])
    self.drop_down_status.items = items
    self.drop_down_status.selected_value = current
    # Enabled only if a next state is available and record exists
    self.drop_down_status.enabled = (len(items) > 1) and bool(self.pbom_id)

  def drop_down_status_change(self, **e):
    if not self.pbom_id:
      # Cannot change status before the record exists
      self._bind_status_dropdown("draft")
      return

    old = self._status
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

  def _bind_rev_dropdown(self, current_rev, is_archived):
    # Provide [current_rev, next_rev]; when no current_rev (brand new), offer ["A"]
    next_rev = self._next_alpha_rev(current_rev or "")
    items = []
    if current_rev:
      items.append(current_rev)
    if next_rev and next_rev != current_rev:
      items.append(next_rev)
    if not items:
      items = ["A"]

    self.drop_down_rev.items = items
    self.drop_down_rev.selected_value = current_rev if current_rev in items else items[0]
    # Enabled if:
    #  - record exists, not archived, and we have a "next" option; OR
    #  - record does not yet exist (new mode) so user can choose initial rev
    self.drop_down_rev.enabled = (not is_archived and len(items) > 1 and bool(self.pbom_id)) or (not self.pbom_id)

  def drop_down_rev_change(self, **e):
    # New mode: selecting rev just sets the eventual initial rev for create()
    if not self.pbom_id:
      self._rev = self.drop_down_rev.selected_value or "A"
      return

    # Existing mode: selecting the next rev clones via revise_from
    current_rev = self.doc.get("rev") or ""
    selected_rev = self.drop_down_rev.selected_value or current_rev
    if selected_rev == current_rev:
      return
    try:
      clone = anvil.server.call("pbomtpl_revise_from", self.pbom_id, selected_rev)
      if clone:
        open_form("PBOMTemplateRecord", pbom_id=clone["_id"])
    except Exception as ex:
      alert(f"Failed to create revision: {ex}")
      self.drop_down_rev.selected_value = current_rev

  def _next_alpha_rev(self, cur):
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
        else:
          chars[i] = chr(ord(chars[i]) + 1)
          carry = False
      return ("A" + "".join(chars)) if carry else "".join(chars)
    m = re.fullmatch(r"(.*?)(\d+)$", cur)
    if m:
      head, digits = m.groups()
      return f"{head}{int(digits)+1:0{len(digits)}d}"
    return cur + "A"

  # ---------- Lines ----------

  def button_regenerate_click(self, **e):
    if self._status != "draft":
      Notification("Can only regenerate lines while in draft.").show()
      return
    if confirm("Rebuild lines from DesignBOM? This will replace current lines."):
      anvil.server.call("pbomtpl_regenerate_from_design", self.pbom_id)
      self._load()
