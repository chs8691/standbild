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

# stats key delimeter. This character may not be used in the location's values (coutntry, region, city, plz)!
deli = '|'

# Default treshold for number of posts for a location group
treshold = 10

# Name of the post markdown file
INDEXFILENAME = 'index.md'

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

    log(f'get_address()')

    ret = dict()

    try:
        geolocator = Nominatim(user_agent="de.kollegen.standbild")
        location = geolocator.reverse(coordinates)
        log(f"Fetched location: {location}")
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


def read_image(item, address):
    """
    Adds image attributes to item. Return item added with keys from tags.py.
        DATE: As datetime object 
    address: Boolean if address data should be read from geopy/Nominatim
    """

    ret = item

    filename = os.path.join(item[T.DIR], item[T.NAME])

    log(f'read_image() {filename}')

    ret[T.TITLE      ] = 'ohne Titel' 
    ret[T.DESCRIPTION] = '' 
    ret[T.MAKE       ] = 'unbekannt' 
    ret[T.MODEL      ] = 'unbekannt' 
    ret[T.LENS       ] = 'unbekannt' 
    ret[T.ALBUM      ] = None
    ret[T.ALBUM_DIR  ] = None
    ret[T.POST       ] = None 
    ret[T.SOOC       ] = 'False' 
    ret[T.BW         ] = 'False' 
    ret[T.LAT        ] = '' 
    ret[T.LON        ] = '' 
    ret[T.CITY       ] = '' 
    ret[T.PLZ        ] = '' 

    # 
    ret[T.COUNTRY    ] = '' 
    ret[T.STATE      ] = '' 
    ret[T.REGION     ] = '' 

    # Will not be set here
    ret[T.LOCATION   ] = ''

    # Fuji X specific tags: Will only be set for X-Cameras
    ret[T.FILMSIMULATION] = '' 
    ret[T.RECIPE     ] = '' 
    ret[T.RECIPE_SOURCE] = '' 

    dt = None

    with ExifToolHelper() as et:

        values = et.get_metadata(filename)[0]
        # log(f'values={values}')

        field = 'EXIF:DateTimeOriginal'
        if field in values:
            dt = datetime.strptime(values[field], '%Y:%m:%d %H:%M:%S')

        # Workaraound for missing datetime: Parse filename. This should always start with date and time 
        else:
            print('WARN Missing EXIF:DateTimeOriginal, parsing filename')
            dt = datetime.strptime(re.sub('[^0-9]', '', filename)[:14], '%Y%m%d%H%M%S')
        
        ret[T.DATE] = dt.strftime("%Y-%m-%dT%H:%M:%S")
        ret[T.YEAR] = dt.year
        ret[T.POST] = dt.strftime("%Y%m%d-%H%M%S")

        field = 'EXIF:ImageDescription'
        if field in values:
            ret[T.DESCRIPTION] = values[field]

        field = 'XMP:Caption'
        if field in values:
            ret[T.TITLE] = values[field]
            
        field = 'EXIF:Make'
        if field in values:
            ret[T.MAKE] = values[field]
            
        field = 'EXIF:Model'
        if field in values:
            ret[T.MODEL] = values[field]
            
        field = 'EXIF:LensModel'
        if field in values:
            ret[T.LENS] = values[field]

        # W or E  
        field = 'EXIF:GPSLongitudeRef'
        if field in values:
            ref = values[field]

        field = 'EXIF:GPSLongitude'
        if field in values:
            if ref == 'W':
             ret[T.LON] = - values[field]
            else:
             ret[T.LON] = values[field]

        # N or S 
        field = 'EXIF:GPSLongitudeRef'
        if field in values:
            ref = values[field]

        field = 'EXIF:GPSLatitude'
        if field in values:
            ret[T.LAT] = values[field]
            if ref == 'S':
             ret[T.LAT] = - values[field]
            else:
             ret[T.LAT] = values[field]

        if address:
            addr = get_address(ret[T.LAT], ret[T.LON])

            key = T.STATE
            for key in [T.STATE, T.COUNTRY, T.REGION, T.CITY, T.PLZ]:
                if key in addr:
                    ret[key] = addr[key]

        tagname = 'XMP:TagsList'
        data = et.get_tags(filename, tags=[tagname])
        log(f'data: {data}')

        if len(data) > 0 and tagname in data[0]:

            # For single item, a String will be returned, otherwise it is a list!
            tags = data[0][tagname]

            # Wrap single entry as list    
            if isinstance(tags, str):
                tags = [tags]

            # log(f'TAGS: {tags}')

            for tag in tags:
                if tag == 'SOOC':
                    ret[T.SOOC] = True

            p = re.compile('Serie/(.*)')
            for tag in tags:
                m = p.match(tag)
                if m is not None:
                    ret[T.ALBUM] = m.group(1)
                continue

            # Older images don't use 'Serie/'
            if ret[T.ALBUM] is None: 
                for key in ['Orte', 'die-runde-stunde', 'pendel', 
                            'kollegenrunde', 'GN', 'Home Spot', 
                            'Wettkampftag', 'Brompt_on the way']:
                    if key in tags:
                        ret[T.ALBUM] = key


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
                    ret[T.FILMSIMULATION] = m.group(2)
                    hasfilm = True
                    
                    if m.group(1) != 'Color':
                        ret[T.BW] = True

                    # log(f'tag: {tag}')

                continue

            if T.SOOC in ret and not T.RECIPE in ret:
                warn('SOOC but no Recipe')
    
            if not T.SOOC in ret and T.RECIPE in ret:
                warn('Recipe but not SOOC')
    
            if not hasfilm:
                warn('Missing film simulation')

        # FUJIFILM specific tags 
        if ret[T.MAKE].lower() == 'fujifilm':

            if len(ret[T.FILMSIMULATION]) == 0:
                ret[T.FILMSIMULATION] = 'unbekannt'

            if len(ret[T.RECIPE]) == 0:
                ret[T.RECIPE] = 'ohne'
                ret[T.RECIPE_SOURCE] = ''

            elif len(ret[T.RECIPE_SOURCE]) == 0:
                ret[T.RECIPE_SOURCE] = 'unbekannt'
            
            
    if ret[T.ALBUM] is None:
        ret[T.ALBUM] = 'Single'
        warn('Missing Tag for Serie. Set ALBUM="Single"')

    ret[T.ALBUM_DIR] = re.sub('[^0-9a-zA-Z]+', '-', ret[T.ALBUM].lower())
    log(f'Serie (Album): {ret[T.ALBUM]}')

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

    if(p.suffix.lower() != '.jpg' and p.suffix.lower() == '.jpeg'):
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
    if args.verbose or args.veryverbose:
        print(message)

def vlog(message):
    if args.veryverbose:
        print(message)


def warn(message):
        print(f'WARN {message}')

    
def write_index_file(filename, image):
    """Replace index.md to write index data into frontmatter. The parameters will be checked first. Return False in error case."""

    vlog(f'write_index_file(): {filename}')
    vlog(f'image={image}')

    # First preopare all data before b) changing the file. This gives the chance to detect issues like missng items.
    lines = []

    # Like all other frontmatter values: may not end with a \n to prevnent for empty lines
    if image[T.DESCRIPTION].endswith('\n'):
        description = image[T.DESCRIPTION][0:-2]
    else:
        description = image[T.DESCRIPTION]

    lines.append('---')
    lines.append(f'{T.TITLE}: {image[T.TITLE]}')
    lines.append(f'{T.DATE}: {image[T.DATE]}')
    # lines.append(f'album: {image[T.ALBUM]}')
    # lines.append(f'album-dir: {image[T.ALBUM_DIR]}')
    lines.append(f'{T.YEAR}: {image[T.YEAR]}')
    lines.append(f'{T.RECIPE}: {image[T.RECIPE]}')
    lines.append(f'{T.RECIPE_SOURCE}: {image[T.RECIPE_SOURCE]}')
    lines.append(f'{T.MAKE}: {image[T.MAKE]}')
    lines.append(f'{T.LENS}: {image[T.LENS]}')
    lines.append(f'{T.MODEL}: {image[T.MODEL]}')
    lines.append(f'{T.SOOC}: {image[T.SOOC]}')
    lines.append(f'{T.FILMSIMULATION}: {image[T.FILMSIMULATION]}')
    lines.append(f'{T.BW}: {image[T.BW]}')
    lines.append(f'{T.DESCRIPTION}: >')
    lines.append(f'{description}')
    # lines.append(f"type: 'photo'")
    lines.append(f'{T.LAT}: {image[T.LAT]}')
    lines.append(f'{T.LON}: {image[T.LON]}')
    lines.append(f'{T.COUNTRY}: {image[T.COUNTRY]}')
    lines.append(f'{T.STATE}: {image[T.STATE]}')
    lines.append(f'{T.REGION}: {image[T.REGION]}')
    lines.append(f'{T.CITY}: {image[T.CITY]}')
    lines.append(f'{T.PLZ}: {image[T.PLZ]}')
    lines.append(f'{T.LOCATION}: {image[T.LOCATION]}')
    lines.append('---')

    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'w') as f:
        for line in lines:
            f.write(f'{line}\n')

    log(f'{filename} created')

    return True


def formatting_description(description):
    """Frontmatter valid and human readable text."""

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

    # Patch for reciper.py: Remove title for settings if empty
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


def process_import(images, address):
    log('process_import()')

    for image in images:
        image = read_image(image, address)
        prepare_tmp(args.source, tmp)
        filename = os.path.join(args.source, tmp, INDEXFILENAME)

        image[T.DESCRIPTION] = formatting_description(image[T.DESCRIPTION])
        if write_index_file(filename, image):
            # continue
            create_image(args.source, tmp, image[T.NAME])
            create_post(args.destination, image[T.ALBUM_DIR], image[T.POST], args.source, tmp, image[T.NAME], INDEXFILENAME)
            rm_import_image(args.source, image[T.NAME])




def read_source_images(source):
    """Returns list of dictionary with keys name, dir."""
    images = []

    log('read_source_images()')

    for folder, subfolders, files in os.walk(source):
        # log(f'{folder}')
        for f in [f for f in files if f.lower().endswith('jpg') or f.lower().endswith('jpeg')]:
            item = {T.NAME: f, T.DIR: folder}
            images.append(item)
            log(f'  {item}')
    
    return images




def loc_create_index_from_files(root):
    """Parse posts for index.md files for location data. Returns a list with dictionary for every post. With None value for NEW_LOCATION."""

    ret = []
    count_non_gps = 0
    count_non_location = 0
    count_non_country = 0

    log('create_index_from_files()')

    for folder, subfolders, files in os.walk(root):
        # log(f'{folder}')
        for f in [f for f in files if f.lower() == INDEXFILENAME]:

            filename = os.path.join(folder, f)
            with open(filename) as file:
                item = {T.NAME: filename, 
                        T.LAT: None,
                        T.LON: None,
                        T.COUNTRY: None,
                        T.STATE: None,
                        T.REGION: None,
                        T.PLZ: None,
                        T.CITY: None,
                        T.LOCATION: None,

                        # Will not  be filled here
                        T.NEW_LOCATION: None,
                        }
                
                for line in file:
                    for key in [T.LAT, T.LON, T.COUNTRY, T. STATE, T.REGION, T.PLZ, T.CITY, T.LOCATION]:
                        if line.startswith(f'{key}:'):
                            value = line.replace(f'{key}: ', '').replace('\n', '').strip()
                            if len(value) > 0:
                                item[key] = value

            if item[T.LAT] is None or item[T.LON] is None:
                count_non_gps += 1
                vlog(f'Missing GPS: {filename}')
            
            if item[T.COUNTRY] is None:
                count_non_country += 1
                vlog(f'Missing Country: {filename}')
            
            if item[T.LOCATION] is None:
                count_non_location += 1
                # vlog(f'Missing Location: {filename}')

            ret.append(item)
            # log(f'  {item}')
    
    log(f'Found {len(ret)} files "{INDEXFILENAME}". Missing GPS={count_non_gps}, missing Country={count_non_country}, missing Location={count_non_location}')

    return ret


def loc_create_stats(index, fields):
    """
    Count occurance of places for the give field pair and its treshold (index 2). Return dict with occurances as key (keys) and value (counter). 
    To have just one key value both values, for field[0] and field [1], will be used as a tuple.
    """

    log('loc_create_stats')

    all = dict()
    ret = dict()
    cnt = 0

    for i in [i for i in index if i[T.NEW_LOCATION] is None]:
        # log(f'i={i}')

        k = (i[fields[0]], i[fields[1]])
        treshold = fields[2]

        cnt += 1
        if k in all:
            all[k] += 1
        else:
            all[k] = 1

#   Fetch the relevant items
    for (key, value) in [(key, value) for (key, value) in all.items() if value >= treshold]:
        ret[key] = value

    log(f'Status for {fields}. Parsed {cnt} items. stats={ret}')

    return ret


def loc_set_new_location(index, stats, fields):
    """ Set field new_location by matching stats for the give key fields. Returns the updated index."""

    ret = index
    cnt = 0

    for s in stats:  
        for i in [i for i in ret if i[T.NEW_LOCATION] is None]:
            if i[fields[0]] == s[0] and i[fields[1]] == s[1]:
                cnt += 1
                i[T.NEW_LOCATION] = s[0]
                # log(i[T.NEW_LOCATION])

    log(f'loc_set_new_location: Set for {cnt} items')

    return ret       


def loc_read_frontmatter(filename):
    """Returns frontmatter data from the give file as dict like in write_index_file(). Returns None in any problem case."""

    vlog('loc_read_frontmatter()')

    if not os.path.exists(filename):
        print(f'WARN Skipping non existing file {filename}')

    item = {}
    with open(filename) as file:

        fm = None
        desc = None
        description = ''

        p = re.compile('^(\\w+): (.*)\n')
        
        for line in file:

            vlog(f'line={line}')

            # Entering frontmatter
            if fm is None and line.startswith('---'):
                vlog('Entering frontmatter')
                fm = True
                continue

            # Exit frontmatter
            if fm is True and line.startswith('---'):
                vlog('Exit frontmatter')
                fm = False
                break

            # Entering one time multiline description
            if desc is None and line.startswith('description: >'):
                vlog('Entering description')
                desc = True
                continue

            # Read description line until next item  
            if desc:
                if line.startswith('  '):
                    vlog('Read description line')
                    description = description + line
                    continue
                else:
                    desc = False



            # Normal item mode
            m = p.match(line)
            if m is not None:
                vlog('Normal item mode')
                item[m.group(1)] = m.group(2)

        item[T.DESCRIPTION] = description

    vlog(f'item={item}')

    return item


def loc_update_index_files(index):
    """ Update location in index.md if changed. """
    missing = 0
    changed = 0
    total = 0

    vlog('loc_update_index_files()')

    for i in index:
        total += 1
        if T.NEW_LOCATION not in i:
            missing += 1
            continue

        if i[T.NEW_LOCATION] != i[T.LOCATION]:
            changed += 1

            # Take existing values...
            item = loc_read_frontmatter(i[T.NAME])
            vlog(f'item from loc_read_frontmatter={item}')

            # and just update location if changed
            item[T.LOCATION] = i[T.NEW_LOCATION]
            ret = write_index_file(i[T.NAME], item)
    
    #    # TEST TEST ETST STTE ETTS ETST TEST
    #     if total >= 10:
    #         break
            

    print(f'Location updated: total={total}, changed={changed}, missing={missing}')


def loc_process(root, treshold):

    vlog('loc_process()')

    index = loc_create_index_from_files(root)
    # log(f'index={index}')

    # Get all nearest areas and count occurance of them
    for fields in [(T.CITY, T.PLZ, treshold), (T.REGION, T.STATE, treshold), (T.STATE, T.COUNTRY, treshold), (T.COUNTRY, T.COUNTRY, 1)]:
        stats = loc_create_stats(index, fields)

        # Set location for matching items
        index = loc_set_new_location(index, stats, fields)

    loc_update_index_files(index)

    # vlog(f'index={index}')


def main():

    parseargs()

    if not os.path.isdir(args.destination):
        exit(f'Destination directory not found: {args.destination}')
    
    if not args.source is None:
    
        images = read_source_images(args.source)

        if len(images) == 0:
            exit(f'No image found in: {args.source}')

        process_import(images, args.address)

    if args.location:
        loc_process(args.destination, args.treshold)   

    log('Done.')
    

def parseargs():
    global args
    parser = argparse.ArgumentParser(description="Creates in root directory of 'destination' a photo directory with image and index.md file." \
                                     " Existing files and directories of 'destination' will be overwritten!" \
                                     " The index file of the touched album will be refreshed." \
                                     " The featured tag will be recalculated to album with the newest file.")
    parser.add_argument('-a', '--address', action='store_true', help=f'Retrieve address by gps coordinates from Nominatim.' )
    parser.add_argument('-l', '--location', action='store_true', help=f'Update location taxonomy in post processing. This flag is independent of the import.' )
    parser.add_argument('-t', '--treshold', type=int, default=treshold, help=f'Number of posts to group them as a term for the location taxonomy. Default is {treshold}.' )
    parser.add_argument('-v', '--verbose', action='store_true', help=f'Print more information' )
    parser.add_argument('-vv', '--veryverbose', action='store_true', help=f'Print all information' )
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