from anvil import *
import anvil.server
import re
from ._anvil_designer import PBOMTemplateRecordTemplate

class PBOMTemplateRecord(PBOMTemplateRecordTemplate):
  """
  Production BOM Template Record

  Modes:
    - New (pbom_id is None): blank header; operator types parent_id in text_parent_id
      and presses Enter to resolve parent details. "Create PBOM" button becomes enabled
      once parent is valid. No DB document exists until creation.
    - Existing (pbom_id provided): loads document; header fields auto-save on change
      while status == 'draft'.

  Status transitions:
    draft -> active -> obsolete -> archived

  Revision selector:
    [current_rev, next_rev]; selecting next_rev clones a new draft via pbomtpl_revise_from.
  """

  def __init__(self, pbom_id: str | None,
               parent_prefix="",
               status="",
               rev="",
               plant="",
               **kwargs):
    self.init_components(**kwargs)
    self.pbom_id = pbom_id
    self.doc = {}

    # UI roles
    self.repeating_panel_lines.role = "scrolling-panel"
    self.button_home.role = "mydefault-button"
    self.button_regenerate.role = "new-button"
    self.button_create.role = "save-button"

    # Wire events
    self.text_parent_id.set_event_handler("pressed_enter", self._resolve_parent_on_enter)
    self.text_plant.set_event_handler("change", self.text_plant_change)
    self.text_variant.set_event_handler("change", self.text_variant_change)
    self.text_notes.set_event_handler("change", self.text_notes_change)

    # If creating new, prepare a blank header; else load from DB
    if self.pbom_id:
      self._load()
    else:
      self._init_new_blank(parent_prefix, status, rev, plant)

  # ---------- New-record (unsaved) mode ----------

  def _init_new_blank(self, parent_prefix, status, rev, plant):
    # Clear all header UI
    self.label_id.text = "(unsaved)"
    self.label_status.text = "draft"
    self.text_parent_id.text = ""  # Operator enters this
    self.label_parent_desc.text = ""
    self.text_rev.text = (rev or "").strip() or "A"
    self.text_plant.text = (plant or "").strip()
    self.text_variant.text = ""
    self.text_notes.text = ""

    # New mode: enable all header fields for entry
    for c in [self.text_parent_id, self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = True

    # Buttons / lines visibility
    self.button_create.visible = True
    self.button_create.enabled = False  # becomes enabled once parent resolves
    self.button_regenerate.visible = False  # not until saved
    self.repeating_panel_lines.items = []   # no lines yet

    # Status & revision dropdowns reflect draft, but rev-change is irrelevant until saved
    self._bind_status_dropdown("draft")
    self._bind_rev_dropdown(self.text_rev.text, is_archived=False)
    self.drop_down_rev.enabled = False

  def _resolve_parent_on_enter(self, **e):
    """When operator enters parent_id and presses Enter, fetch and show dependent data."""
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      Notification("Enter a valid parent_id.").show()
      return
    try:
      # Keep this generic and light-weight; you may swap for your existing parts getter.
      part = anvil.server.call("get_part_brief", pid)  # expected: {"part_id","description",...} or None
    except Exception as ex:
      alert(f"Lookup failed: {ex}")
      return

    if not part:
      self.label_parent_desc.text = ""
      self.button_create.enabled = False
      Notification("Parent not found.").show()
      return

    self.label_parent_desc.text = part.get("description") or part.get("part_name") or ""
    # Enable create now that we have a resolvable parent
    self.button_create.enabled = True

  def button_create_click(self, **e):
    """
    Create a draft PBOM document from header fields.
    Lines can be generated later via 'Regenerate from DesignBOM'.
    """
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      Notification("Enter a valid parent_id first.").show()
      return

    payload = {
      "parent_part_id": pid,
      "rev": (self.text_rev.text or "A").strip(),
      "plant_id": (self.text_plant.text or None) or None,
      "variant": (self.text_variant.text or None) or None,
      "notes": (self.text_notes.text or None) or None,
    }
    try:
      # New server helper for this flow:
      # - Creates a draft PBOM with minimal header
      # - Enforces uniqueness (parent_part_id + rev) server-side
      # - Returns full doc including _id
      created = anvil.server.call("pbomtpl_create_draft", payload)
    except Exception as ex:
      alert(f"Create failed: {ex}")
      return

    if not created:
      alert("Create failed (no document returned).")
      return

    # Re-open in existing mode
    open_form("PBOMTemplateRecord", pbom_id=created["_id"])

  # ---------- Existing-record mode ----------

  def _load(self):
    d = anvil.server.call("pbomtpl_get", self.pbom_id) or {}
    self.doc = d

    # Header bindings
    self.label_id.text             = d.get("_id", "")
    self.text_parent_id.text       = d.get("parent_part_id", "") or ""
    self.label_parent_desc.text    = d.get("parent_desc", "") or ""
    status                         = d.get("status", "draft")
    rev                            = d.get("rev") or ""
    self.text_rev.text             = rev
    self.text_plant.text           = d.get("plant_id") or ""
    self.text_variant.text         = d.get("variant") or ""
    self.text_notes.text           = d.get("notes") or ""
    self.label_status.text         = status

    is_draft = (status == "draft")
    # Inputs enabled only while draft
    for c in [self.text_parent_id, self.text_rev, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    # Buttons
    self.button_create.visible = False
    self.button_regenerate.visible = True
    self.button_regenerate.enabled = is_draft

    # Status / Revision controls
    self._bind_status_dropdown(status)
    is_archived = (status == "archived")
    self._bind_rev_dropdown(rev, is_archived)

    # Lines
    self.repeating_panel_lines.items = d.get("lines", [])

  # ---------- Header autosave (existing + draft) ----------

  def _save_header(self, patch: dict):
    if not patch:
      return
    if not self.pbom_id:
      # In new/unsaved mode, the header isn't in DB yet; nothing to save.
      return

    if self.label_status.text != "draft":
      Notification("Header is read-only (status ≠ draft).").show()
      return
    try:
      self.doc = anvil.server.call("pbomtpl_update", self.pbom_id, patch)
      self._load()
    except Exception as e:
      alert(f"Save failed: {e}")

  def text_parent_id_change(self, **e):
    """
    Allow changing parent while draft. Keep behavior explicit:
    - Resolve parent description for UI feedback.
    - Save to DB if in existing draft mode.
    """
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      self.label_parent_desc.text = ""
      return
    try:
      part = anvil.server.call("get_part_brief", pid)
      self.label_parent_desc.text = (part or {}).get("description") or (part or {}).get("part_name") or ""
    except Exception:
      self.label_parent_desc.text = ""
    # Persist (existing + draft)
    self._save_header({"parent_part_id": pid})

  def text_plant_change(self, **e):
    self._save_header({"plant_id": (self.text_plant.text or None) or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": (self.text_variant.text or None) or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": (self.text_notes.text or None) or None})

  # ---------- Status & Revision ----------

  def _bind_status_dropdown(self, current: str):
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
    if not self.pbom_id:
      # No status changes until created
      self.drop_down_status.selected_value = "draft"
      return

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
    self.drop_down_rev.enabled = (not is_archived) and (len(items) > 1) and bool(self.pbom_id)

  def drop_down_rev_change(self, **e):
    if not self.pbom_id:
      # In new mode, rev is just a text field; dropdown disabled.
      return

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

  def _next_alpha_rev(self, cur: str) -> str:
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
    if self.label_status.text != "draft":
      Notification("Can only regenerate lines while in draft.").show()
      return
    if confirm("Rebuild lines from DesignBOM? This will replace current lines."):
      anvil.server.call("pbomtpl_regenerate_from_design", self.pbom_id)
      self._load()



