#!/usr/bin/env python3
"""find files to migrate"""


# import libraries
import os
import glob
import time
import subprocess
import cv2
import wxcutils


def find_latest_directory(directory):
    """find latest directory in directory"""
    latest = 0
    for directories in os.listdir(directory):
        if int(directories) > latest:
            latest = int(directories)
    return str(latest)


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory):
        directory_set.append(directories)
    return directory_set


def crawl_images(ci_directory):
    """crawl directory structure for all images
    of the data type directory"""
    # start at base, get list of all dates
    date_directories = find_directories(base_dir)

    # go through the right directory, find the files
    for dir in date_directories:
        dir_dir = os.path.join(os.path.join(base_dir, dir), ci_directory)
        for file in glob.glob(os.path.join(dir_dir, '*.*')):
            bits = os.path.split(file)
            l_filename, l_extenstion = os.path.splitext(bits[1])
            sub_bits = l_filename.split('_')
            # IMG_FD_014_IR105_20200808_022006
            # only add the FD images to the index
            if len(sub_bits) == 6:
                MY_LOGGER.debug('dir = %s, file = %s, ext = %s, date = %s, time = %s',
                                bits[0], l_filename, l_extenstion, sub_bits[4], sub_bits[5])
                FILES.append({'dir': bits[0], 'file': l_filename, 'ext': l_extenstion,
                              'datetime': sub_bits[4] + sub_bits[5]})


def find_latest_file(directory):
    """find latest file in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        if '_sanchez' not in filename:
            file_timestamp = os.path.getmtime(os.path.join(directory, filename))
            if file_timestamp > latest_timestamp:
                latest_filename = filename
                latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f',
                    latest_filename, latest_timestamp)
    return latest_filename


def clahe_process(cp_in_path, cp_in_file, cp_out_path, cp_out_file):
    """clahe process the file using OpenCV library"""
    def clahe(in_img):
        """do clahe create processing on image"""
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(in_img)

    def do_clahe_img(in_img):
        """do clahe merge processing on image"""
        b_chn, g_chn, r_chn = cv2.split(in_img)
        return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

    MY_LOGGER.debug('clahe_process %s %s %s %s', cp_in_path, cp_in_file,
                    cp_out_path, cp_out_file)
    MY_LOGGER.debug('process image')
    cp_out_img = do_clahe_img(cv2.imread(cp_in_path + cp_in_file))
    MY_LOGGER.debug('write new image')
    cv2.imwrite(cp_out_path + cp_out_file, cp_out_img)
    MY_LOGGER.debug('write image complete')


def create_thumbnail(ct_directory, ct_extension):
    """create thumbnail of the image"""
    wxcutils.run_cmd('convert \"' + OUTPUT_PATH + ct_directory +
                     ct_extension +  '\" -resize 9999x500 ' +
                     OUTPUT_PATH + ct_directory + '-tn' + ct_extension)


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def animate(a_directory, a_filename, a_extenstion, a_frames, a_suffix):
    """create animation file"""
    def add_txt(at_path, at_file, add_duration):
        """add text"""

        if add_duration:
            line = 'file \'' + at_path + '/' + at_file + '\'' + \
                os.linesep + 'duration 0.05' + os.linesep
        else:
            line = 'file \'' + at_path + '/' + at_file + '\'' + os.linesep
        return line

    MY_LOGGER.debug('directory = %s, filename = %s, extenstion = %s, frames = %d, suffix = %s',
                    a_directory, a_filename, a_extenstion, a_frames, a_suffix)
    a_files = len(FILES)
    if a_frames > a_files:
        a_frames = a_files
        MY_LOGGER.debug('Reduced frames to %d as not enough frames exist (max = %d)',
                        a_frames, a_files)
    a_text = ''

    MY_LOGGER.debug('Going throught the last %d frames', a_frames)
    if a_suffix != '':
        a_suffix = '_' + a_suffix
    a_counter = a_files - a_frames
    while  a_counter < a_files:
        a_text = a_text + add_txt(FILES[a_counter]['dir'], FILES[a_counter]['file'] + a_suffix + FILES[a_counter]['ext'], True)
        if not os.path.exists(FILES[a_counter]['dir'] + '/' + FILES[a_counter]['file'] + \
            a_suffix + FILES[a_counter]['ext']):
            # need to generate file
            if a_suffix == '_sanchez':
                MY_LOGGER.debug('sanchez file to create')
                MY_LOGGER.debug('/home/pi/sanchez/Sanchez -s ' + FILES[a_counter]['dir'] + '/' +
                                FILES[a_counter]['file'] + FILES[a_counter]['ext'] +
                                ' -m /home/pi/sanchez/Resources/Mask.jpg -u /home/pi/sanchez/Resources/GK-2A/Underlay.jpg -o ' + \
                                FILES[a_counter]['dir'] + '/' + FILES[a_counter]['file'] + a_suffix + \
                                FILES[a_counter]['ext'] + ' -t 0070BA')
                wxcutils.run_cmd('/home/pi/sanchez/Sanchez -s ' + FILES[a_counter]['dir'] + \
                    '/' + FILES[a_counter]['file'] + FILES[a_counter]['ext'] + \
                    ' -m /home/pi/sanchez/Resources/Mask.jpg -u /home/pi/sanchez/Resources/GK-2A/Underlay.jpg -o ' + \
                    FILES[a_counter]['dir'] + '/' + FILES[a_counter]['file'] + a_suffix + FILES[a_counter]['ext'] + ' -t 0070BA')
            else:
                MY_LOGGER.debug('%s file to create', a_suffix)
        a_counter += 1
    # add last frame again, but with no duration
    a_text += add_txt(FILES[a_files - 1]['dir'], FILES[a_files - 1]['file'] + a_suffix + FILES[a_files - 1]['ext'], False)

    # save as a file
    wxcutils.save_file(WORKING_PATH, 'framelist.txt', a_text)

    # create animation
    if a_suffix == '':
        a_suffix = 'raw'
    wxcutils.run_cmd('ffmpeg -y -safe 0 -f concat -i ' + WORKING_PATH +
                     'framelist.txt -c:v libx264 -pix_fmt yuv420p -vf scale=800:800 ' + OUTPUT_PATH + 'FD-' +
                     a_suffix + '-' + str(a_frames) + '.mp4')

    # create file with date time info
    date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    wxcutils.save_file(OUTPUT_PATH, 'FD-' + a_suffix + '-' + str(a_frames) + '.txt', date_time)


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'

# start logging
MODULE = 'find_files'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')
MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('CODE_PATH = %s', CODE_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('OUTPUT_PATH = %s', OUTPUT_PATH)
MY_LOGGER.debug('IMAGE_PATH = %s', IMAGE_PATH)
MY_LOGGER.debug('WORKING_PATH = %s', WORKING_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)


# try:
# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]

base_dir = '/home/pi/gk-2a/xrit-rx/received/LRIT/'
MY_LOGGER.debug('base_dir = %s', base_dir)

# load latest times data
latest_timestamps = wxcutils.load_json(OUTPUT_PATH, 'gk2a_info.json')

# find latest directory
date_directory = find_latest_directory(base_dir)
MY_LOGGER.debug('latest directory = %s', date_directory)

date_base_dir = os.path.join(base_dir, date_directory)
data_directories = find_directories(date_base_dir)

# data store for files list
# currently just for FD
FILES = []

# find latest file in each directory and copy to output directory
for directory in data_directories:
    MY_LOGGER.debug('---------------------------------------------')
    MY_LOGGER.debug('directory = %s', directory)
    location = os.path.join(date_base_dir, directory)
    MY_LOGGER.debug('location = %s', location)
    latest_file = find_latest_file(location)
    MY_LOGGER.debug('latest_file = %s', latest_file)
    filename, extenstion = os.path.splitext(latest_file)
    MY_LOGGER.debug('extenstion = %s', extenstion)

    # date time for original file
    latest = os. path. getmtime(os.path.join(location, latest_file))
    MY_LOGGER.debug('latest = %d', latest)
    latest_local = wxcutils.epoch_to_local(latest, '%a %d %b %H:%M')
    MY_LOGGER.debug('latest_local = %s', latest_local)

    stored_timestamp = 0.0
    try:
        stored_timestamp = latest_timestamps[directory + extenstion]
    except NameError:
        pass
    except KeyError:
        pass

    # REMOVE REMOVE REMOVE
    # if directory == 'FD':
    #     stored_timestamp = 0

    MY_LOGGER.debug('stored_timestamp = %f, %f', stored_timestamp, latest)
    if stored_timestamp != int(latest):
        MY_LOGGER.debug('New %s file added', directory)
        latest_timestamps[directory + extenstion] = int(latest)

        # copy file to the output directory
        wxcutils.copy_file(os.path.join(location, latest_file), os.path.join(OUTPUT_PATH, directory + extenstion))

        # create thumbnail
        create_thumbnail(directory, extenstion)

        # create file with date time info
        date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
        if directory != 'ANT':
            wxcutils.save_file(OUTPUT_PATH, directory + '.txt', date_time)
        else:
            wxcutils.save_file(OUTPUT_PATH, 'ANT.txt.txt', date_time)

        # additional processing of FD image
        if directory == 'FD':
            # crawl directories for all files
            crawl_images(directory)
            # sort
            FILES = sorted(FILES, key=lambda k: k['datetime'])
            # save to file system for debugging only
            # wxcutils.save_json(WORKING_PATH, 'crawl.json', FILES)
            animate(directory, filename, extenstion, 143, '')
            animate(directory, filename, extenstion, 143, 'sanchez')
            animate(directory, filename, extenstion, 143 * 5, '')
            animate(directory, filename, extenstion, 143 * 5, 'sanchez')

            # CLAHE processing
            clahe_process(OUTPUT_PATH, 'FD.jpg', OUTPUT_PATH, 'clahe.jpg')
            create_thumbnail('clahe', extenstion)
            date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
            wxcutils.save_file(OUTPUT_PATH, 'clahe.txt', date_time)

            # sanchez processing
            # image should have been created already for the animations
            MY_LOGGER.debug('Checking for %s', os.path.join(location, filename + '_sanchez' + extenstion))
            if os.path.isfile(os.path.join(location, filename + '_sanchez' + extenstion)):
                MY_LOGGER.debug('File already exists, copy it')
                wxcutils.copy_file(os.path.join(location, filename + '_sanchez' + extenstion), os.path.join(OUTPUT_PATH, 'sanchez.jpg'))
            else:
                MY_LOGGER.debug('File does not exist, create it')
                wxcutils.run_cmd('/home/pi/sanchez/Sanchez -s ' + OUTPUT_PATH + 'clahe.jpg -m /home/pi/sanchez/Resources/Mask.jpg -u /home/pi/sanchez/Resources/GK-2A/Underlay.jpg -o ' + OUTPUT_PATH + 'sanchez.jpg -t 0070BA -f')
            create_thumbnail('sanchez', extenstion)
            date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
            wxcutils.save_file(OUTPUT_PATH, 'sanchez.txt', date_time)


    else:
        MY_LOGGER.debug('File unchanged')

# save latest times data
wxcutils.save_json(OUTPUT_PATH, 'gk2a_info.json', latest_timestamps)

# rsync files to servers
wxcutils.run_cmd('rsync -rt ' + OUTPUT_PATH + ' mike@192.168.100.18:/home/mike/wxcapture/gk-2a')
wxcutils.run_cmd('rsync -rt ' + base_dir + ' pi@192.168.100.15:/home/pi/goes/gk-2a')


# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
