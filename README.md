# Facebook Photo Downloader
This tool lets you download all of the Facebook photos that you are tagged in. It keeps track of the dates that each photo was uploaded to Facebook, so that your photos will still be organized by date when they are added to a digital photo organized like Google Photos or iPhoto.

![Metadata Example](https://raw.githubusercontent.com/jcontini/fb-photo-downloader/master/example.png)

The script does this in 2 steps:
1) Create an index of all the photos and metadata (date, description, etc)
2) Download all of the photos and write metadata to them (EXIF)

## Installation
1. Clone this repository
1. `cd` into the cloned folder 
1. Run `pip install -r requirements.txt`

This tool uses Google Chrome to download the photos, so be sure to [install Chrome](https://www.google.com/chrome/) before using.

## Usage
To download your tagged photos, run this with your FB username & password:

`python get-tagged-photos.py -u your@email.com -p yourpassword`

You should see Chrome open, login to Facebook, navigate to your photos page, and indexing your tagged photos & videos. Once the indexing is complete, it will download all of the photos to a `photos` folder that should appear in the same folder as the script.

### Index-Only mode

If you just want to create an index of the photos so you can see the data, add the `--index` flag:

`python get-tagged-photos.py --index -u your@email.com -p yourpassword`

### Download-Only mode

If you already have the index and want to download the images again, you can run the script in download-only mode like this:

`python get-tagged-photos.py --download`

The credentials are not needed for download-only mode because Facebook lets anyone access the photos once you have the direct URL to the photo. Facebook can expire a URL after some time though, so if there are any issues with the downloading, try indexing again first to make sure the script has the latest photo URLs.

## More Details
This script works by first creating an index of all the photos that you are tagged in with:

- Date the photo was uploaded
- Photo description (caption)
- Names tagged in the photo
- Facebook URL of the photo page
- Photo URL to the actual image
- Name, Profile URL, and user ID of the person who uploaded the photo

All of this metadata is only stored on your computer, and you can see it in `tagged.json`. Once the indexing process is complete, the script will then download all of the photos to your computer, and then use this index to write the metadata to them so that it's safe with the photo file.