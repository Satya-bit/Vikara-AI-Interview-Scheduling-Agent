import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Final

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from schemas import ScheduleRequest, ScheduleResponse
from vapi import VapiClient


def setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


setup_logging()
logger = logging.getLogger(__name__)
load_dotenv()
REQUIRED_ENV_VARS: Final[tuple[str, ...]] = ("VAPI_API_KEY", "VAPI_ASSISTANT_ID", "VAPI_PHONE_NUMBER_ID")


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        self.vapi_api_key = os.getenv("VAPI_API_KEY", "")
        self.vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID", "")
        self.vapi_phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID", "")

    def validate(self) -> None:
        values = {
            "VAPI_API_KEY": self.vapi_api_key,
            "VAPI_ASSISTANT_ID": self.vapi_assistant_id,
            "VAPI_PHONE_NUMBER_ID": self.vapi_phone_number_id,
        }
        missing = [key for key in REQUIRED_ENV_VARS if not values[key]]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def get_settings() -> Settings:
    return Settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.validate()
    logger.info("Application started in %s mode", settings.app_env)
    yield


app = FastAPI(title="Vikara AI Interview Scheduling Agent", version="1.0.0", lifespan=lifespan)


settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Future use: re-enable this in-memory store when adding a debug/admin endpoint
# to inspect recent scheduling requests without a database.
# candidate_store: list[CandidateRecord] = []


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Future use:  We can re-enable this helper when candidate persistence/reporting is needed. We can also have a database in future to record them and store it in database
# def store_candidate(payload: ScheduleRequest) -> None:
#     candidate_store.append(
#         CandidateRecord(
#             name=payload.name,
#             email=payload.email,
#             phone=payload.phone,
#             created_at=datetime.now(tz=timezone.utc),
#         )
#     )


@app.post("/schedule", response_model=ScheduleResponse)
async def schedule_interview(payload: ScheduleRequest, cfg: Settings = Depends(get_settings)) -> ScheduleResponse:
   
    # In-memory candidate storage is currently disabled; outbound call flow does not depend on it currently. For future use only.
    # store_candidate(payload)

    vapi = VapiClient(
        api_key=cfg.vapi_api_key,
        assistant_id=cfg.vapi_assistant_id,
        phone_number_id=cfg.vapi_phone_number_id,
    )
    try:
        call_data = await vapi.trigger_outbound_call(
            phone=payload.phone,
            name=payload.name,
            email=payload.email,
        )
    except Exception as exc:
        logger.exception("Failed to initiate Vapi call for %s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to initiate outbound call: {exc}",
        ) from exc

    call_id = call_data.get("id") or call_data.get("call", {}).get("id")
    return ScheduleResponse(status="call_initiated", call_id=call_id)
