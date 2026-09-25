"""Serve the coffee machine in a browser.

This layer is deliberately outside the specification: nothing here is
specified and nothing here is tested. It imports the real CoffeeMachine and
calls the same request_brew() the tests call, then ships the resulting state
to the page. The browser draws that state and decides nothing on its own.

It also watches src/ and reloads it in place, so the picture follows the code
while you are editing it, and it reads the requirement sentence from spec/
on every update, so the page never shows words the file no longer says.
"""

import asyncio
import hashlib
import importlib
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from coffee_machine import brew_control, machine as machine_module, model, telemetry
from tools import spec_loader

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
SOURCE_FILE = ROOT / "src" / "coffee_machine" / "brew_control.py"
SPEC_FILE = ROOT / "spec" / "REQ-BREW-014.md"
RESULTS_FILE = ROOT / ".demo" / "results.json"
HEARTBEAT_SECONDS = 2
# How long the pour stays on screen. Presentation only: the machine has
# already decided and filled the cup by the time the picture starts.
POUR_SECONDS = 3

_subscribers: set[asyncio.Queue] = set()


@asynccontextmanager
async def lifespan(_: FastAPI):
    watcher = asyncio.create_task(watch_sources())
    yield
    watcher.cancel()


app = FastAPI(title="Coffee machine", lifespan=lifespan)


class Session:
    """Holds the live machine, and rebuilds it whenever the code changes."""

    def __init__(self) -> None:
        self.machine = machine_module.CoffeeMachine()
        self.state = "idle"
        self.brew_count = 0

    def rebuild(self) -> None:
        """Re-create the machine from the freshly reloaded classes.

        An instance built before the reload still belongs to the old class,
        so keeping it would show stale behaviour while the badge showed a new
        hash. Carry the hardware state across, drop everything else.
        """
        level_ml = self.machine.tank.level_ml
        capacity_ml = self.machine.tank.capacity_ml
        self.machine = machine_module.CoffeeMachine(
            tank=model.Tank(level_ml=level_ml, capacity_ml=capacity_ml)
        )
        self.state = "idle"


session = Session()


def source_sha() -> str:
    return hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()[:6]


def spec_sentence() -> dict:
    try:
        requirement = spec_loader.load(SPEC_FILE)
    except (OSError, ValueError):  # a half-written file is normal while typing
        return {"uid": SPEC_FILE.stem, "text": ""}
    return {"uid": requirement.uid, "text": requirement.text}


def test_results() -> dict:
    try:
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"passed": 0, "failed": 0, "first_failure": None}


def payload(kind: str = "state") -> dict:
    snapshot = telemetry.snapshot(session.machine, session.state)
    snapshot["type"] = kind
    snapshot["src_sha"] = source_sha()
    snapshot["source"] = SOURCE_FILE.read_text(encoding="utf-8")
    sentence = spec_sentence()
    snapshot["spec_uid"] = sentence["uid"]
    snapshot["spec_text"] = sentence["text"]
    snapshot["tests"] = test_results()
    return snapshot


async def broadcast(kind: str = "state") -> None:
    message = payload(kind)
    for queue in list(_subscribers):
        queue.put_nowait(message)


@app.get("/api/stream")
async def stream(request: Request):
    """One unnamed event type for everything.

    Named SSE events never reach onmessage, and a silently missing listener
    is a miserable thing to debug on a deadline, so the kind travels inside
    the JSON instead.
    """
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.add(queue)

    async def events():
        try:
            yield f"data: {json.dumps(payload())}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_SECONDS
                    )
                except asyncio.TimeoutError:
                    message = payload("heartbeat")
                yield f"data: {json.dumps(message)}\n\n"
        finally:
            _subscribers.discard(queue)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/select")
async def select(body: dict):
    try:
        drink = model.Drink[str(body.get("drink", "ESPRESSO")).upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="no such drink")
    result = session.machine.request_brew(drink)
    session.state = "brewing" if result.brew_started else "refusing"
    session.brew_count += 1
    if result.brew_started:
        asyncio.create_task(finish_pour(session.brew_count))
    await broadcast()
    return {"ok": True}


async def finish_pour(brew: int) -> None:
    """Stop the pour, leave the coffee in the cup.

    Any later action changes the state or starts another brew, and then this
    one must not touch the picture.
    """
    await asyncio.sleep(POUR_SECONDS)
    if session.brew_count == brew and session.state == "brewing":
        session.state = "served"
        await broadcast()


@app.post("/api/tank")
async def set_tank(body: dict):
    capacity_ml = session.machine.tank.capacity_ml
    level_ml = int(body.get("level_ml", 0))
    session.machine.tank.level_ml = max(0, min(level_ml, capacity_ml))
    session.machine.display.warning = model.Warning.NONE
    session.state = "idle"
    session.machine.cup_ml = 0
    await broadcast()
    return {"ok": True}


@app.post("/api/refill")
async def refill(_: dict):
    """Filling the tank is the machine's own business, not the browser's."""
    session.machine.refill()
    session.state = "idle"
    session.machine.cup_ml = 0
    await broadcast()
    return {"ok": True}


async def watch_sources() -> None:
    """Reload the package in place, then rebuild the machine."""
    from watchfiles import awatch

    async for _ in awatch(ROOT / "src", ROOT / "spec", ROOT / ".demo", step=300):
        try:
            importlib.reload(model)
            importlib.reload(brew_control)
            importlib.reload(machine_module)
            session.rebuild()
        except Exception as error:  # a half-written file is normal while typing
            print(f"reload skipped: {error}")
            continue
        await broadcast("reload")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


app.mount("/", StaticFiles(directory=STATIC), name="static")
