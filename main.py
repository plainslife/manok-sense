#!/usr/bin/env python3
# main.py - entry point: boots the hardware and runs the state machine

import time
import src.boot     as boot
import src.settings_store as settings
from src.ui.display   import DisplayUI
from src.ui.animation import Animation
from src.hardware.distance  import DistanceSensor
from src.context   import AppContext

# state modules 
from src.states import preview
from src.states import capture
from src.states import process
from src.states import result
from src.states import settings  as settings_state
from src.states import gallery
from src.states import gallery_preview

# state registry
# maps state name strings to their module. adding a new state only requires
# adding one line here and creating the corresponding state module.
_STATES = {
    "preview":         preview,
    "capturing":       capture,
    "processing":      process,
    "result":          result,
    "settings":        settings_state,
    "gallery":         gallery,
    "gallery_preview": gallery_preview,
}


def main() -> None:
    # boot sequence
    display   = DisplayUI()
    animation = Animation(display)

    animation.show_splash()
    time.sleep(1.2)

    led, cam, touch = boot.run(animation)

    # load persited settings
    cfg    = settings.load()
    sensor = DistanceSensor()

    # build shared context
    ctx = AppContext(cam, display, animation, touch, led, sensor, cfg)

    # Re-init distance sensor if it was enabled in the last session
    if cfg["distance_enabled"]:
        print("[Main] Distance sensor enabled in settings — attempting boot init")
        ctx.sensor_active = sensor.try_init(3.0)
        if not ctx.sensor_active:
            print("[Main] Sensor not found at boot — disabling for this session")

    animation.show_ready()
    time.sleep(0.8)

    # state machine loop
    current_state = "preview"
    prev_state    = None

    try:
        while True:
            now = time.monotonic()

            # call on_enter() whenever we transition into a new state
            if current_state != prev_state:
                _STATES[current_state].on_enter(ctx)
                prev_state = current_state

            # run the current state — it returns the name of the next state
            next_state = _STATES[current_state].run(ctx, now)

            current_state = next_state

    except KeyboardInterrupt:
        print("\nExiting")

    finally:
        sensor.shutdown()
        led.off()
        cam.stop()
        display.shutdown()


if __name__ == "__main__":
    main()
