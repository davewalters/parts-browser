from ._anvil_designer import PurchaseOrderLinesTemplate
from anvil import *
import anvil.server


class PurchaseOrderLines(PurchaseOrderLinesTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
