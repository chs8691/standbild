import argparse
import os
from pathlib import Path
import tags as T
from exiftool import ExifToolHelper
import re
from datetime import datetime
from PIL import Image, ImageOps
from geopy.geocoders import Nominatim

# Use args in the top level functions
args = None

# root directory to write to
destination = 'content'

# Source directory with images directly and in sub directories. Non-JPGs and other files will be ignored
source = 'import'

# Self-managed subdirectory for file creations 
tmp = 'tmp'

# Name of the post markdown file
indexfile = 'index.md'

def create_image(source, tmp, name):
    """
        Create full size image for one image from the import folder
        All things will be done in the source folders subdirectory 'tmp'.
        In error case, exit() will be executed.
    """

    # log(f'create_image()')

    full_width = 1900   
    filename = os.path.join(source, name)

    try:
        with Image.open(filename) as im:
            # Must be rotated by exif Orientation, otherwise thumb and full will not be
            # shown the image in the correct rotation
            # log('ImageOps.exif_transpose')
            im = ImageOps.exif_transpose(im)
            concat = full_width/float(im.size[0])
            size = int((float(im.size[1])*float(concat)))
            # print(f"concat,size={concat}, {size}")
            # log('Rezising now')
            out = im.resize((full_width,size), resample=Image.Resampling.LANCZOS)
            out.save(os.path.join(source, tmp, name), "JPEG")

    except OSError:
        err(f"Cannot convert image {filename}!  ")
        

def get_address(latitude, longitude, language="de"):

    coordinates = f"{latitude}, {longitude}"

    ret = dict()

    try:
        geolocator = Nominatim(user_agent="de.kollegen.standbild")
        location = geolocator.reverse(coordinates)
        log(f"get_address() {location}")
        parts = location.address.split(", ")
        if len(parts) >= 5:
            ret[T.COUNTRY] = parts[-1]
            ret[T.STATE] = parts[-3]
            ret[T.REGION] = parts[-4]
            ret[T.PLZ] = parts[-2]
            ret[T.CITY] = parts[-5]
        elif len(parts) >= 2:
            ret[T.COUNTRY] = parts[-1]
            ret[T.STATE] = parts[-2]
        else:
            ret[T.COUNTRY] = parts
    except:
        print("geolocator failed")

    return ret

def read_image(item):
    """
    Adds image attributes to item. Return item added with keys from tags.py.
        DATE: As datetime object 
    """

    ret = item

    filename = os.path.join(item[T.DIR], item[T.NAME])

    ret[T.TITLE      ] = 'ohne Titel' 
    ret[T.DESCRIPTION] = '' 
    ret[T.MODEL      ] = 'unbekannt' 
    ret[T.ALBUM      ] = 'Single' 
    ret[T.ALBUM_DIR  ] = 'single' 
    ret[T.POST       ] = None 
    ret[T.FILM       ] = 'unbekannt' 
    ret[T.RECIPE     ] = '' 
    ret[T.RECIPE_SOURCE] = '' 
    ret[T.SOOC       ] = 'False' 
    ret[T.BW         ] = 'False' 
    ret[T.LAT        ] = '' 
    ret[T.LON        ] = '' 
    ret[T.COUNTRY    ] = '' 
    ret[T.STATE      ] = '' 
    ret[T.REGION     ] = '' 
    ret[T.CITY       ] = '' 
    ret[T.PLZ        ] = '' 

    dt = None

    with ExifToolHelper() as et:

        values = et.get_metadata(filename)[0]
        # log(f'values={values}')

        field = 'EXIF:DateTimeOriginal'
        if field in values:
            dt = datetime.strptime(values[field], '%Y:%m:%d %H:%M:%S')
        else:
            err('Missing EXIF:DateTimeOriginal')
        
        ret[T.DATE] = dt.strftime("%Y-%m-%dT%H:%M:%S")
        ret[T.YEAR] = dt.year
        ret[T.POST] = dt.strftime("%Y%m%d-%H%M%S")
            
        field = 'EXIF:ImageDescription'
        if field in values:
            ret[T.DESCRIPTION] = values[field]

        field = 'XMP:Caption'
        if field in values:
            ret[T.TITLE] = values[field]
            
        field = 'EXIF:Model'
        if field in values:
            ret[T.MODEL] = values[field]

        field = 'EXIF:GPSLongitude'
        if field in values:
            ret[T.LON] = values[field]

        field = 'EXIF:GPSLatitude'
        if field in values:
            ret[T.LAT] = values[field]

        addr = get_address(ret[T.LAT], ret[T.LON])

        key = T.STATE
        for key in [T.STATE, T.COUNTRY, T.REGION, T.CITY, T.PLZ]:
            if key in addr:
                ret[key] = addr[key]

        tagname = 'XMP:TagsList'
        data = et.get_tags(filename, tags=[tagname])
        log(f'data: {data}')

        if len(data) > 0 and tagname in data[0]:

            tags = data[0][tagname]

            for tag in tags:

                if tag == 'SOOC':
                    ret[T.SOOC] = True

            p = re.compile('Serie/(.*)')
            for tag in tags:
                m = p.match(tag)
                if m is not None:
                    ret[T.ALBUM] = m.group(1)
                continue

            p = re.compile('Recipe/(.*)')
            for tag in tags:
                m = p.match(tag)
                if m is not None:
                    parts = m.group(1).split('/')
                    if(len(parts) < 2):
                        ret[T.RECIPE] = parts[0]
                    else:
                        ret[T.RECIPE] = parts[1]
                        ret[T.RECIPE_SOURCE] = parts[0]
                continue

            hasfilm = False
            p = re.compile('(?:Fujifilm|Fuji-X)/(BW|Black&White|Color)/(.*)')
            for tag in tags:
                m = p.match(tag)

                if m is not None:
                    ret[T.FILM] = m.group(2)
                    hasfilm = True
                    
                    if m.group(1) != 'Color':
                        ret[T.BW] = True

                    # log(f'tag: {tag}')

                continue

            if not T.ALBUM in ret:
                ret[T.ALBUM] = 'Single'
                warn('Missing Tag for Serie. Set ALBUM="SINGLE"')

            ret[T.ALBUM_DIR] = re.sub('[^0-9a-zA-Z]+', '-', ret[T.ALBUM].lower())

            if T.SOOC in ret and not T.RECIPE in ret:
                warn('SOOC but no Recipe')
    
            if not T.SOOC in ret and T.RECIPE in ret:
                warn('Recipe but not SOOC')
    
            if not hasfilm:
                warn('Missing film simulation')

            

    log(f'item={ret}' )

    return ret
    

def err(msg):
    print(f'ÉRROR {msg}')
    exit(1)

def copy_image(content_dir, path):
    """ 
    Copy image to a new photo directory with an album and creates index.md file with image metadata. Existing data will be overwritten.
    Argument content_dir must be an full path to an image file within an album.
    """

    p = Path(path)

    if(len(p.parts)< 2):
        err(f"Path doesn't contain album and image: {path}")

    if(not p.suffix.lower() == '.jpg'):
        err(f"Invalid image format: {str(p.suffix)}. Must be an jpg file")
   
    tags = dict()

    with ExifToolHelper() as et:
        values = et.get_metadata(path)[0];
 
        field = 'EXIF:ImageDescription'
        if field in values:
            tags[T.DESCRIPTION] = values[field]

        log(f'tags={tags}' )

    print(f'process_image {path}')


def log(message):
    if args.verbose:
        print(message)


def warn(message):
        print(f'WARN {message}')


def make_dir(image):
    """Creates local direcory, ready to move."""

    print(image[T.DATE])

def create_index_file(source, tmp, image, index):

    filename = os.path.join(source, tmp, index)

    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'w') as f:
        f.write('---\n')
        f.write(f'title: {image[T.TITLE]}\n')
        f.write(f'date: {image[T.DATE]}\n')
        # f.write(f'album: {image[T.ALBUM]}\n')
        # f.write(f'album-dir: {image[T.ALBUM_DIR]}\n')
        f.write(f'year: {image[T.YEAR]}\n')
        f.write(f'recipe: {image[T.RECIPE]}\n')
        f.write(f'recipe_source: {image[T.RECIPE_SOURCE]}\n')
        f.write(f'model: {image[T.MODEL]}\n')
        f.write(f'sooc: {image[T.SOOC]}\n')
        f.write(f'filmsimulation: {image[T.FILM]}\n')
        f.write(f'bw: {image[T.BW]}\n')
        f.write(f'description: >\n')
        f.write(f'{formatting_description(image[T.DESCRIPTION])}\n')
        f.write(f"type: 'photo'\n")
        f.write(f'lat: {image[T.LAT]}\n')
        f.write(f'lon: {image[T.LON]}\n')
        f.write(f'country: {image[T.COUNTRY]}\n')
        f.write(f'state: {image[T.STATE]}\n')
        f.write(f'region: {image[T.REGION]}\n')
        f.write(f'CITY: {image[T.CITY]}\n')
        f.write(f'PLZ: {image[T.PLZ]}\n')
        f.write('---\n')

    log(f'{filename} created for {image[T.NAME]}')

def formatting_description(description):

    # log('prepare_description()')
    lines = description.split('\n')
    ok = True

    # Remove empty top lines 
    while(ok and len(lines) > 0):  
        if len(lines[0]) == 0:
                # log('pop')
                lines.pop(0) 
        else:
            ok = False

    ok = True

    # Remove title for settings if empty
    while(ok and len(lines) > 0):
        if(lines[-1] == 'Divergent settings:' or len(lines[-1]) == 0):
            lines.pop()
        else:
            ok = False

    ret = ''
    eol = ''
    for l in lines:
        ret = ret + eol + '    ' + l
        eol = '\n'

    return ret

def prepare_tmp(source, tmp):

    log('prepare_tmp()')
    dir = os.path.join(source, tmp)

    if not os.path.exists(dir):
        os.mkdir(dir)
        return

    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))

    # log('tmp is now empty')


def create_post(destination, album, post, source, tmp, filename, index):

    log('create_post()')
    dir = os.path.join(destination, album)

    if not os.path.exists(dir):
        err(f'Album directory not found. Please, create it first and run script again: {dir}')

    dir = os.path.join(dir, post)

    if os.path.exists(dir):

        log(f'Existing post found in: {dir}')

        for f in os.listdir(dir):
            log(f'Removing file: {f}')
            os.remove(os.path.join(dir, f))

    else:
        log(f'Creating post directory: {dir}')
        os.mkdir(dir)

    source_dir = os.path.join(source, tmp)
    log(f'Moving post files: {filename}, {index}')
    os.rename(os.path.join(source_dir, filename), os.path.join(dir, filename))
    os.rename(os.path.join(source_dir, index), os.path.join(dir, index))


def rm_import_image(source, filename):

    path = os.path.join(source, filename)

    log(f'Removing {path}')
    os.remove(path)


def process(images):
    log('process()')

    for image in images:
        image = read_image(image)
        prepare_tmp(args.source, tmp)
        create_index_file(args.source, tmp, image, indexfile)
        create_image(args.source, tmp, image[T.NAME])
        create_post(args.destination, image[T.ALBUM_DIR], image[T.POST], args.source, tmp, image[T.NAME], indexfile)
        rm_import_image(args.source, image[T.NAME])




def read_source_images(source):
    """Returns list of dictionary with keys name, dir."""
    images = []

    log('read_source_images()')

    for folder, subfolders, files in os.walk(source):
        # log(f'{folder}')
        for f in [f for f in files if f.lower().endswith('jpg')]:
            item = {T.NAME: f, T.DIR: folder}
            images.append(item)
            log(f'  {item}')
    
    return images

def main():

    parseargs()

    if not os.path.isdir(args.destination):
        exit(f'Destination directory not found: {args.destination}')
    
    # if not os.path.isdir(args.source):
    #     exit(f'Source directory not found: {args.source}')
    
    images = read_source_images(args.source)

    if len(images) == 0:
        exit(f'No image found in: {args.source}')

    process(images)

    log('Done.')
    

def parseargs():
    global args
    parser = argparse.ArgumentParser(description="Creates in root directory of 'destination' a photo directory with image and index.md file." \
                                     " Existing files and directories of 'destination' will be overwritten!" \
                                     " The index file of the touched album will be refreshed." \
                                     " The featured tag will be recalculated to album with the newest file.")
    parser.add_argument('-v', '--verbose', action='store_true', help=f'Print more information' )
    parser.add_argument('-d', '--destination', type=str, 
                        help=f"Content directory as root where to merge to. Default is {destination}." \
                        " The subdirectory is taken from he image's tag 'album'." \
                        " Existing posts will be replaced", 
                        default=destination )
    parser.add_argument('-s', '--source', type=str, 
                        help=f"Path to the import diretcory with images to be processed." \
                        "The images must be tagged at least with 'album', otherwise 'Singels' will be used." )
    args = parser.parse_args()


if __name__ == "__main__":
    main()