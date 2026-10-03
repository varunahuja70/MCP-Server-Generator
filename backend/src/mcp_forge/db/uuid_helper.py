"""RFC 9562 compliant UUIDv7 generation with monotonic counter."""

import os
import threading
import time
import uuid

_lock = threading.Lock()
_last_v7_ts = 0
_v7_counter = 0


def uuidv7() -> str:
    """Generate a strictly time-ordered UUIDv7 string.

    48 bits: unix timestamp in milliseconds
    4 bits: version (7)
    12 bits: monotonic counter within millisecond
    2 bits: variant (2)
    62 bits: random
    """
    global _last_v7_ts, _v7_counter

    with _lock:
        nanos = time.time_ns()
        timestamp_ms = nanos // 1_000_000

        if timestamp_ms > _last_v7_ts:
            _last_v7_ts = timestamp_ms
            _v7_counter = 0
        else:
            _v7_counter += 1
            timestamp_ms = _last_v7_ts

        ts_bytes = timestamp_ms.to_bytes(6, byteorder="big")
        counter_int = _v7_counter & 0x0FFF
        counter_bytes = counter_int.to_bytes(2, byteorder="big")
        rand_bytes = bytearray(os.urandom(8))

        var_bytes = bytearray([counter_bytes[0], counter_bytes[1]]) + rand_bytes
        # Version 7: set high 4 bits of octet 6 to 0111
        var_bytes[0] = (var_bytes[0] & 0x0F) | 0x70
        # Variant 1: set high 2 bits of octet 8 to 10
        var_bytes[2] = (var_bytes[2] & 0x3F) | 0x80

        full_bytes = ts_bytes + var_bytes
        return str(uuid.UUID(bytes=bytes(full_bytes)))


def utcnow_iso() -> str:
    """Return current UTC time in ISO-8601 string format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
