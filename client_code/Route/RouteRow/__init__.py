# client_code/RouteRow/__init__.py
from anvil import *
from ._anvil_designer import RouteRowTemplate

class RouteRow(RouteRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_open_details.role = "mydefault-button"

  def form_show(self, **event_args):
    route = self.item or {}
    self.label_route_id.text = route.get("_id", "")
    self.label_route_name.text = route.get("route_name", "")
    self.label_route_description.text = route.get("description", "")

    # Build a readable summary of routing (sequence + cell_name)
    routing = route.get("routing") or []
    # Route list returns cell_id; for display we prefer cell_name.
    # If the server included cell_name (recommended), use it; otherwise fallback to id.
    def step_to_text(step):
      seq = step.get("sequence_number", "")
      name = step.get("cell_name") or step.get("cell_id") or ""
      return f"{seq} {name}".strip()

    summary_items = [step_to_text(s) for s in sorted(routing, key=lambda x: x.get("sequence_number", 10))]
    # Optional: limit length for very long routes
    max_tokens = 8
    if len(summary_items) > max_tokens:
      summary_items = summary_items[:max_tokens] + ["…"]

    self.label_routing_summary.text = " \u2192 ".join(summary_items)  # → arrows

