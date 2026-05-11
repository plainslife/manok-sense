# src/context.py - shared application context passed to every state

from config import DISTANCE_MIN_CM, DISTANCE_MAX_CM


def _get_distance_state(cm: int | None) -> str:
    """Classify a distance reading into ok / near / far."""
    if cm is None:
        return "far"
    if cm < DISTANCE_MIN_CM:
        return "near"
    if cm > DISTANCE_MAX_CM:
        return "far"
    return "ok"


class AppContext:
    """
    Single object that holds all shared hardware references and mutable
    state. Passed as the only argument to every state's run() function,
    which removes the need to pass ten individual parameters everywhere.
    """

    def __init__(self, cam, display, animation, touch, led, sensor, cfg: dict) -> None:

        # hardware
        self.cam       = cam
        self.display   = display
        self.animation = animation
        self.touch     = touch
        self.led       = led
        self.sensor    = sensor

        # persisted settings
        self.cfg           = cfg
        self.sensor_active = False

        # debounce
        self.last_touch = 0.0

        # camera failure counter
        self.cam_fail_count = 0

        # capture / inference data
        self.captured_frames:  list         = []
        self.result:           tuple | None = None
        self.result_frames:    list         = []
        self.result_frame_idx: int          = 0

        # gallery navigation data
        self.gallery_sessions:   list = []
        self.gallery_page:       int  = 0
        self.gallery_session_idx: int = 0
        self.gallery_frame_idx:   int = 0

    # helpers

    def debounced(self, now: float, secs: float = 0.4) -> bool:
        """Return True if enough time has passed since the last touch."""
        return (now - self.last_touch) > secs

    def read_distance(self) -> tuple[int | None, str]:
        """
        Read the distance sensor if active.
        Automatically disables the sensor if it disconnects mid-session.
        Returns (distance_cm, distance_state).
        """
        if not self.sensor_active:
            return None, "ok"

        cm = self.sensor.get_cm()

        if not self.sensor.is_ok:
            self.sensor_active = False
            print("[Context] Distance sensor disconnected — running without it")

        return cm, _get_distance_state(cm)
