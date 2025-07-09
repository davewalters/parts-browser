import anvil.server

# Detect if running inside the Anvil editor or deployed environment
IS_ANVIL_HOSTED = not anvil.server.is_local()

# Define environment-specific URLs
LOCAL_API_BASE_URL = "http://127.0.0.1:8000"
DEV_API_BASE_URL = "https://your-dev-server.com"
PROD_API_BASE_URL = "https://your-production-api.com"

# Choose the correct one based on environment
if IS_ANVIL_HOSTED:
  API_BASE_URL = PROD_API_BASE_URL  # Or DEV_API_BASE_URL if not yet in production
else:
  API_BASE_URL = LOCAL_API_BASE_URL

