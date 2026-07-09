import os

TOKEN = os.getenv("TOKEN")

# Safely get and convert the ADMIN_ID
admin_id_raw = os.getenv("ADMIN_ID")
ADMIN_ID = int(admin_id_raw) if admin_id_raw else None
