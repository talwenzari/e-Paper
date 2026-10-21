#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import sys
import time
from pathlib import Path
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


from PIL import Image
from waveshare_epd import epd7in5_V2


DEFAULT_POLL_INTERVAL = 30.0


def load_display_image(image_path: Path, width: int, height: int) -> Image.Image:
    image = Image.open(image_path)
    if image.mode != '1':
        image = image.convert('1')
    if image.size != (width, height):
        image = image.resize((width, height))
    # #region agent log
    try:
        import json, time
        pixels = image.load()
        bands = []
        for band in range(4):
            x0 = band * image.width // 4
            x1 = (band + 1) * image.width // 4
            black = 0
            total = 0
            for y in range(0, image.height, 4):
                for x in range(x0, x1, 4):
                    total += 1
                    if pixels[x, y] == 0:
                        black += 1
            bands.append(round(black / total, 3) if total else None)
        _payload = {"sessionId": "b27ad5", "runId": "post-fix-vcom", "hypothesisId": "A", "location": "epd_7in5_V2_watch.py:load_display_image", "message": "buffer black fraction left to right", "data": {"mode": image.mode, "size": list(image.size), "blackFractionByQuarter": bands}, "timestamp": int(time.time() * 1000)}
        logging.info("debug %s", json.dumps(_payload))
        _line = json.dumps(_payload) + "\n"
        _paths = [Path(r"c:\Users\TuomasTalvensaari\Repos\e-Paper\.cursor\debug-b27ad5.log"), Path(__file__).resolve().parents[3] / ".cursor" / "debug-b27ad5.log"]
        for _path in _paths:
            try:
                _path.parent.mkdir(parents=True, exist_ok=True)
                with open(_path, "a", encoding="utf-8") as _f:
                    _f.write(_line)
            except Exception:
                pass
    except Exception:
        pass
    # #endregion
    return image


def get_file_signature(image_path: Path) -> float:
    return image_path.stat().st_mtime


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    script_dir = Path(__file__).resolve().parent
    default_picture_dir = script_dir.parent / 'pic'
    default_image = default_picture_dir / '7in5_V2.bmp'

    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_image
    poll_interval = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_POLL_INTERVAL

    logging.info('Starting epd_7in5_V2_watch')
    logging.info('Watching image: %s', image_path)
    logging.info('Poll interval: %s seconds', poll_interval)

    if not image_path.is_absolute():
        image_path = (Path.cwd() / image_path).resolve()

    epd = epd7in5_V2.EPD()
    last_signature = None
    has_displayed = False

    try:
        logging.info('Initializing display')
        epd.init()
        epd.Clear()

        while True:
            if image_path.exists() and image_path.is_file():
                current_signature = get_file_signature(image_path)
                if current_signature != last_signature:
                    logging.info('New or updated image detected, loading %s', image_path)
                    image = load_display_image(image_path, epd.width, epd.height)
                    epd.display(epd.getbuffer(image))
                    last_signature = current_signature
                    has_displayed = True
                else:
                    logging.debug('Image has not changed, skipping refresh')
            else:
                logging.warning('Image file not found: %s', image_path)

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, exiting...')
    except Exception:
        logging.exception('Unexpected error')
    finally:
        try:
            if has_displayed:
                logging.info('Putting display to sleep')
                epd.Clear()
                epd.sleep()
        except Exception:
            logging.exception('Failed to put display to sleep')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
