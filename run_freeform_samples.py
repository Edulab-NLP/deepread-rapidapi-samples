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




def draw_rotated_text(image, angle, xy, text, fill, *args, **kwargs):
    """ Draw text at an angle into an image, takes the same arguments
        as Image.text() except for:

    :param image: Image to write text into
    :param angle: Angle to write text at

    code originally found in answewr supplied by Stephen Rauch here- https://stackoverflow.com/questions/45179820/draw-text-on-an-angle-rotated-in-python
    """
    # get the size of our image
    width, height = image.size
    max_dim = max(width, height)

    # build a transparency mask large enough to hold the text
    mask_size = (max_dim * 2, max_dim * 2)
    mask = Image.new('L', mask_size, 0)

    # add text to mask
    draw = ImageDraw.Draw(mask)
    draw.text((max_dim, max_dim), text, 255, *args, **kwargs)

    if angle % 90 == 0:
        # rotate by multiple of 90 deg is easier
        rotated_mask = mask.rotate(angle)
    else:
        # rotate an an enlarged mask to minimize jaggies
        bigger_mask = mask.resize((max_dim*8, max_dim*8),
                                  resample=Image.BICUBIC)
        rotated_mask = bigger_mask.rotate(angle).resize(
            mask_size, resample=Image.LANCZOS)

    # crop the mask to match image
    mask_xy = (max_dim - xy[0], max_dim - xy[1])
    b_box = mask_xy + (mask_xy[0] + width, mask_xy[1] + height)
    mask = rotated_mask.crop(b_box)

    # paste the appropriate color, with the text transparency mask
    color_image = Image.new('RGBA', image.size, fill)
    image.paste(color_image, mask)


def find_font_size(text_width, text, font_file):
    font_size = text_width
    font = ImageFont.truetype(font_file, font_size)
    size = font.getsize_multiline(text)[0]
    while size > text_width:
        diff = 20 if size - text_width > 100 else 1
        font_size = font_size - diff
        font = ImageFont.truetype(font_file, font_size)
        size = font.getsize_multiline(text)[0]
    return font 


def visualise_ocr(data, original_image, language):
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

    font_file = os.path.join("fonts", "COURIER.ttf")

    if language == 'ja':
        font_file = os.path.join("fonts", "Arial Unicode MS.TTF")

    for area in data['pages'][0]['areas']:
        for para in area['paragraphs']:
            for line in para['lines']:
                vertical_text = line['coordinates']['w'] < line['coordinates']['h']

                for word in line['words']:
                    coords = word['coordinates']
                    text = word['text']
                    bbox = [coords['x'], 
                            coords['y']]
                    
                    if vertical_text:
                        bounding_box_size = math.floor((coords['h']))
                        font = find_font_size(bounding_box_size, text, font_file)
                        draw_rotated_text(output_image, 90, (bbox[0], bbox[1]), text, (0, 0, 0), font=font)
                    else:
                        bounding_box_size = math.floor((coords['w']))
                        font = find_font_size(bounding_box_size, text, font_file)
                        editable_image.text((bbox[0], bbox[1]), text, (0, 0, 0), font=font)
    return hconcat(output_image, original_image)


def process_file(filename, language, key, visualise):
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

    if visualise:
        print('Creating visualisation for {}'.format(filename))
        with Image.open(filename) as original_image:
            output_image = visualise_ocr(data, original_image, language)
            output_image.save(os.path.join(OUTPUT_DIR, os.path.basename(filename)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files with DeepRead.')
    parser.add_argument('-k', '--key', type=str, required=True,
                        help='X-RapidAPI-Key header required to access rapidapi.')
    parser.add_argument('-l', '--language', type=str, default='en',
                        help='ACCEPT-LANGUAGE value passed to rapidapi/deepread.')
    parser.add_argument('--vis', '--visualise', dest='visualise', action='store_true',
                        default=False,
                        help='create visualisation output?')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='path the file to process')
    group.add_argument('--all', dest='all', action='store_true',
                        default=False,
                        help='process all files in samples/ directory?')

    args = parser.parse_args()

    if args.file:
        process_file(args.file, args.language, args.key, args.visualise)
    else:
        for sample in os.listdir(SAMPLES_DIR):
            process_file(os.path.join(SAMPLES_DIR, sample), args.language, args.key, args.visualise)
