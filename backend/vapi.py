import logging
import re
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def normalize_phone_number(value: str) -> str:
    """
    Normalize phone numbers to US E.164 format for Vapi.
    - 10 digits -> +1XXXXXXXXXX
    - 11 digits starting with 1 -> +1XXXXXXXXXX
    """
    raw = value.strip()
    digits = re.sub(r"\D", "", raw)

    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return raw


class VapiClient:
    def __init__(
        self,
        api_key: str,
        assistant_id: str,
        phone_number_id: str,
        base_url: str = "https://api.vapi.ai",
    ):
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.phone_number_id = phone_number_id
        self.base_url = base_url.rstrip("/")

    async def trigger_outbound_call(
        self,
        *,
        phone: str,
        name: str,
        email: str,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/call"
        chosen_assistant_id = self.assistant_id
        chosen_phone_number_id = self.phone_number_id
        normalized_phone = normalize_phone_number(phone)

        base_payload = {
            "assistantId": chosen_assistant_id,
            "customer": {
                "number": normalized_phone,
            },
            "metadata": {
                "name": name,
                "email": email,
            },
            "phoneNumberId": chosen_phone_number_id,
        }

        payload_with_overrides = {
            **base_payload,
            "assistantOverrides": {
                "variableValues": {
                    "name": name,
                    "email": email,
                }
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info("Triggering outbound Vapi call for %s", email)

        async with httpx.AsyncClient(timeout=20.0) as client:
            # First attempt includes dynamic variable overrides for assistant templates.
            response = await client.post(url, json=payload_with_overrides, headers=headers)
            if response.status_code == 400: #fallback to minimal payload if overrides are rejected (some Vapi versions may not support them)
                logger.warning(
                    "Vapi rejected optional override payload. Retrying minimal payload. body=%s",
                    response.text,
                )
                response = await client.post(url, json=base_payload, headers=headers)
            if response.is_error: 
                logger.error("Vapi /call failed: status=%s body=%s", response.status_code, response.text)
            response.raise_for_status()
            return response.json()
