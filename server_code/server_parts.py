import anvil.server
from . import schema_server as models  # Rename to match your Anvil file name

@anvil.server.callable
def save_part_from_client(part_data: dict):
  return models.validate_and_save_part(part_data)

