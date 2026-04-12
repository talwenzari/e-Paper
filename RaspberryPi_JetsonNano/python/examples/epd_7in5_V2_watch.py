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
