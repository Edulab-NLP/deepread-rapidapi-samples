DEEPREAD Free Form - AI OCR - RapidAPI Samples
=============

This repository provides an example Python script along with some sample images to test the DEEPREAD Free Form - AI OCR
RapidAPI endpoints.

Installation
----------
The easiest way to run samples is within a virtual environment using Python3.

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
``` 

Once all the requirements are installed the samples can be processed.

Command line args
-----------
Required params:

`-k`|`--key`: `X-RapidAPI-Key` header required to access rapidapi.

One of these are required:

`--all`: when selected, all images in `samples/` folder will be process.
`-f`|`--file`: to specify a specific file you want to process.

Other args:

`-l`|`--language`: ACCEPT-LANGUAGE value passed to rapidapi/deepread. (default `en`)
`-h`|`--help`: output details of command line inputs.

Usage
----------
To process a specific image:
`python run_freeform_samples.py -k <X-RapidAPI-Key> -f samples/Test_SC7.png`

To process all images in `samples/` folder.
`python run_freeform_samples.py -k <X-RapidAPI-Key> --all`

To process a specific image in japanese:
`python run_freeform_samples.py -k <X-RapidAPI-Key> -f samples/Test_SC7.png -l ja`

Outputs
----------
The script outputs are all sent to the `outputs/` folder.

There are two outputs for every image processed:

i. `outputs/<filename>.<image extension>`: a visualisation of the processed images with side-by-side comparison. The visualisation
places all of the extracted text in the approximate location of the bounding boxes found over a blank image.
ii. `outputs/<filename>.json`: json output returned by DEEPREAD Free Form via RapidAPI.
