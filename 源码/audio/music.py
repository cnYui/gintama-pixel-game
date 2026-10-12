"""Music registry entry point: imports every music module so their @track
decorators run. music_a.py and music_b.py are written by separate composers."""
import importlib
import traceback

for _m in ("audio.music_a", "audio.music_b"):
    try:
        importlib.import_module(_m)
    except ModuleNotFoundError:
        pass
    except Exception:
        print(f"[music] failed to import {_m}")
        traceback.print_exc()
