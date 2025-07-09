import anvil.server
# Set this manually depending on your testing state
ENVIRONMENT = "local"  # or "dev", or "prod"

LOCAL_API_BASE_URL = "http://127.0.0.1:8000"
DEV_API_BASE_URL = "https://your-dev-api.com"
PROD_API_BASE_URL = "https://your-prod-api.com"

# Choose the base URL
if ENVIRONMENT == "local":
  API_BASE_URL = LOCAL_API_BASE_URL
elif ENVIRONMENT == "dev":
  API_BASE_URL = DEV_API_BASE_URL
else:
  API_BASE_URL = PROD_API_BASE_URL



