from __future__ import annotations
import os
from mangum import Mangum
from app.main import app

# Handle API Gateway Stages (e.g. /dev)
stage = os.environ.get("ENV", "dev")
root_path = f"/{stage}" if stage else ""

handler = Mangum(app, api_gateway_base_path=root_path)
