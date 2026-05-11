# src/distance.py

import time

class DistanceSensor:
    def __init__(self) -> None:
        self._tof = None
        self._ok  = False

    # For re init when not working
    def try_init(self, timeout: float = 3.0) -> bool:
        import busio
        import board
        import adafruit_vl53l1x

        deadline = time.monotonic() + timeout
        attempt  = 0

        while time.monotonic() < deadline:
            attempt += 1
            try:
                i2c       = busio.I2C(board.SCL, board.SDA)
                self._tof = adafruit_vl53l1x.VL53L1X(i2c)
                self._tof.start_ranging()
                self._ok  = True
                print(f"[Distance] Sensor ready (attempt {attempt})")
                return True
            except Exception as e:
                print(f"[Distance] Init attempt {attempt} failed: {e}")
                self._tof = None
                time.sleep(0.3)

        self._ok = False
        print("[Distance] No sensor detected — giving up")
        return False

    def get_cm(self) -> int | None:
        if not self._ok or self._tof is None:
            return None
        try:
            d = self._tof.distance
            return int(d) if d is not None else None
        except Exception as e:
            print(f"[Distance] Read error — disabling sensor: {e}")
            self._ok = False
            return None

    @property
    def is_ok(self) -> bool:
        return self._ok

    # ------------------------------------------------------------------ #
    #  Teardown                                                            #
    # ------------------------------------------------------------------ #

    def shutdown(self) -> None:
        if self._tof is not None:
            try:
                self._tof.stop_ranging()
            except Exception:
                pass
        self._ok  = False
        self._tof = None
