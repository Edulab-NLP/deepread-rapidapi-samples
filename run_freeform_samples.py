import argparse
import json
import mimetypes
import os
import requests

import numpy as np
import math
import os
from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = 'outputs'
SAMPLES_DIR = 'samples'


def hconcat(im1, im2):
    """
    Concatenates two images together - for side-by-side comparison.
    """
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


def visualise_ocr(data, original_image):
    """
    Visualise DEEPREAD Free Form response in side-by-side image comparison.
    """
    dims = data['pages'][0]['dimensions']

    height = dims['height']
    width = dims['width']

    img = np.zeros([height, width, 3], dtype=np.uint8)
    img.fill(255) # numpy array!
    output_image = Image.fromarray(img)

    editable_image = ImageDraw.Draw(output_image)

    for area in data['pages'][0]['areas']:
        for para in area['paragraphs']:
            for line in para['lines']:
                for word in line['words']:
                    coords = word['coordinates']
                    bbox = [coords['x'], 
                            coords['y']]

                    bounding_box_size = math.floor((coords['w']))
                    font_size = bounding_box_size
                    font = ImageFont.truetype("Arial Unicode MS.TTF", font_size)
                    size = font.getsize_multiline(word['text'])[0]
                    while size > bounding_box_size:
                        diff = 20 if size - bounding_box_size > 100 else 1
                        font_size = font_size - diff
                        font = ImageFont.truetype("Arial Unicode MS.TTF", font_size)
                        size = font.getsize_multiline(word['text'])[0]

                    editable_image.text((bbox[0], bbox[1]), word['text'], (0, 0, 0), font=font)
    return hconcat(output_image, original_image)


def process_file(filename, language, key):
    """
    Process image with DEEPREAD Free Form RapidAPI endpoint outputting visualisation.
    """
    print('Processing file {}'.format(filename))

    url = "https://deepread-free-form-ai-ocr.p.rapidapi.com/api/v1/ocr"

    headers = {
    	"Accept-Language": language,
    	"X-RapidAPI-Host": "deepread-free-form-ai-ocr.p.rapidapi.com",
    	"X-RapidAPI-Key": key
    }

    with open(filename, 'rb') as file_bytes:
        payload = {
            'source_file': (
                'source_file{}'.format(os.path.splitext(filename)[1]),
                file_bytes,
                mimetypes.guess_type(filename)[0]
            )
        }
        response = requests.post(url, files=payload, headers=headers)

    content = response.text

    data = json.loads(content)['data']

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    json_filename = os.path.join(OUTPUT_DIR, '{}.json'.format(os.path.splitext(os.path.basename(filename))[0]))
    with open(json_filename, 'w') as json_file:
        json_file.write(content)

    with Image.open(filename) as original_image:
        output_image = visualise_ocr(data, original_image)
        output_image.save(os.path.join(OUTPUT_DIR, os.path.basename(filename)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files with DeepRead.')
    parser.add_argument('-k', '--key', type=str, required=True,
                        help='X-RapidAPI-Key header required to access rapidapi.')
    parser.add_argument('-l', '--language', type=str, default='en',
                        help='ACCEPT-LANGUAGE value passed to rapidapi/deepread.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='path the file to process')
    group.add_argument('--all', dest='all', action='store_true',
                        default=False,
                        help='process all files in samples/ directory?')

    args = parser.parse_args()

    if args.file:
        process_file(args.file, args.language, args.key)
    else:
        for sample in os.listdir(SAMPLES_DIR):
            process_file(os.path.join(SAMPLES_DIR, sample), args.language, args.key)
