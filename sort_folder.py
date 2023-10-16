'''
Threads added to:
    - move_and_rename_files()
    - process_dir()

NB about functionality:

- To exit the program, type "*exit" whenever you are asked for an input.

- This script unpacks archives but does not apply the function normilize() to their content and does not delete
empty folders within archives. Only the names of the archives get normalized.

- The destination folder may be the same as the source one (default) or a different one.
- If the destination folder is the same as the source one:
    
    + Folders "archives", "video", "audio", "documents", "images", "other" get created within the same folder which has to
    be sorted.

    + The content of the folders "archives", "video", "audio", "documents", "images", "other" gets sorted if these folders
already exist. However, these folders do not get deleted if they stay empty after sorting.

Possible improvements:
    - Handle files without extensions or raise exception.
    - Normalize files and folders within unpacked archives.
'''

import errno, stat
import os.path
import re
import shutil
import sys

from collections import defaultdict
from os import listdir
from os.path import isfile, join
from threading import Thread

DEFAULT_CATEGORY = "невідомі розширення"
ARCHIVES = "архіви"
IMAGES = "зображення"
VIDEOS = "відео файли"
DOCS = "документи"
AUDIO = "музика"
EXTENSION_2_CATEGORY = defaultdict(lambda: DEFAULT_CATEGORY)

EXTENSIONS_BY_CATEGORY = {
    IMAGES: ('JPEG', 'PNG', 'JPG', 'SVG'),
    VIDEOS: ('AVI', 'MP4', 'MOV', 'MKV'),
    DOCS: ('DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'),
    AUDIO: ('MP3', 'OGG', 'WAV', 'AMR'),
    ARCHIVES: ('ZIP', 'GZ', 'TAR'),
    DEFAULT_CATEGORY: ()
}
CATEGORY_2_FOLDER = {IMAGES: "images",
                     VIDEOS: "video",
                     DOCS: "documents",
                     AUDIO: "audio",
                     ARCHIVES: "archives",
                     DEFAULT_CATEGORY: "other"}

MAPPING_CHARACTERS = {
    "а": "a",  # А
    "б": "b",  # Б
    "в": "v",  # В
    "г": "h",  # Г
    "ґ": "g",  # Ґ
    "д": "d",  # Д
    "е": "e",  # Е
    "є": "ye",  # Є
    "ж": "zh",  # Ж
    "з": "z",  # З
    "и": "y",  # И
    "і": "i",  # І
    "ї": "yi",  # Ї
    "й": "y",  # Й
    "к": "k",  # К
    "л": "l",  # Л
    "м": "m",  # М
    "н": "n",  # Н
    "о": "o",  # О
    "п": "p",  # П
    "р": "r",  # Р
    "с": "s",  # С
    "т": "t",  # Т
    "у": "u",  # У
    "ф": "f",  # Ф
    "х": "kh",  # Х
    "ц": "ts",  # Ц
    "ч": "ch",  # Ч
    "ш": "sh",  # Ш
    "щ": "shch",  # Щ
    "ь": "ʹ",  # Ь
    "ю": "yu",  # Ю

    "я": "ya",  # Я
    "ё": "yo",  # Ё
    "э": "e",  # Э
    "ъ": '"',  # Ъ
    "ы": "y",  # Ы
}
MAPPING_CHARACTERS_CAPITAL = {key.title(): value.upper() for key, value in MAPPING_CHARACTERS.items()}
MAPPING_CHARACTERS.update(MAPPING_CHARACTERS_CAPITAL)
TRANS_TABLE = str.maketrans(MAPPING_CHARACTERS)


def normalize(name: str) -> str:
    name = name.translate(TRANS_TABLE)
    name = re.sub(r"[^0-9a-zA-Z]", "_", name)
    return name


def process_file(file: str, tgt_folder: str, category: str):
    basename = os.path.basename(file)
    filename, extension = basename.rsplit(".", 1)
    new_filename = normalize(filename)
    if not category == ARCHIVES:
        new_file = join(tgt_folder, f"{new_filename}.{extension}")
        shutil.move(file, new_file)  # os.rename(file, new_file)
        # print(new_file)
    else:
        shutil.unpack_archive(file, join(tgt_folder, new_filename))
        os.remove(file)


def move_and_rename_files(categorized_files: dict, path: str):
    threads = []
    for category, files in categorized_files.items():
        folder_name = CATEGORY_2_FOLDER[category]
        tgt_folder = join(path, folder_name)
        if not os.path.exists(tgt_folder):
            os.makedirs(tgt_folder)
        for file in files:
            thread = Thread(target=process_file,
                            args=(file, tgt_folder, category))
            thread.start()
            threads.append(thread)
    [el.join() for el in threads]


# handleRemoveReadonly copied from:
# https://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows
def handleRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise Exception("Problem with removing a read-only file")


def delete_empty_folders(path, ignore=CATEGORY_2_FOLDER.values()):
    content = os.listdir(path)
    # print("content:", content)
    for el in content:
        if el in ignore:
            continue
        el_path = join(path, el)

        for cur_dir, subdirs, files in os.walk(el_path, topdown=False):
            # print(cur_dir, subdirs, files)
            if not subdirs and not files:
                shutil.rmtree(el_path, ignore_errors=False, onerror=handleRemoveReadonly)  # os.rmdir(el_path)


def process_dir(path, files_per_category, known_extensions, unknown_extensions, print_result=True):
    if not EXTENSION_2_CATEGORY:
        for category, extensions in EXTENSIONS_BY_CATEGORY.items():
            for extension in extensions:
                EXTENSION_2_CATEGORY[extension] = category
    threads = []
    for el in listdir(path):
        path_el = join(path, el)
        if isfile(path_el):
            extension = el.rsplit(".", 1)[-1]
            category = EXTENSION_2_CATEGORY[extension.upper()]
            files_per_category[category].append(path_el)
            if category == DEFAULT_CATEGORY:
                unknown_extensions.add(extension)
            else:
                known_extensions.add(extension)
        else:
            thread = Thread(target=process_dir,
                            args=(path_el, files_per_category, known_extensions, unknown_extensions, False))
            thread.start()
            threads.append(thread)
    [el.join() for el in threads]
    if print_result:
        print("ANALYSIS RESULT")
        print(
            "files per category:\n\t" + "\n\t".join([f"{key}: {str(val)}" for key, val in files_per_category.items()]))
        print("known extensions:", known_extensions)
        print("unknown extensions:", unknown_extensions)


def process_exit_request(user_input: str):
    if user_input == "*exit":
        print("You are exiting the programme. Good bye.")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dir_path = input("Please enter the name of the folder to sort: ")
        process_exit_request(dir_path)
    else:
        dir_path = sys.argv[1]
    while not os.path.isdir(dir_path):
        dir_path = input(f"'{dir_path}' is not a valid folder. Please, try again: ")
        process_exit_request(dir_path)
    print("Folder to sort:", dir_path)
    tgt_dir_path = input(f"Please, provide a destination folder (per default: same as the folder to sort): ")
    process_exit_request(tgt_dir_path)
    if not tgt_dir_path:
        tgt_dir_path = dir_path
    print("Destination folder:", tgt_dir_path)
    files_per_category = {category: [] for category in EXTENSIONS_BY_CATEGORY.keys()}
    known_extensions = set()
    unknown_extensions = set()
    process_dir(dir_path, files_per_category, known_extensions, unknown_extensions)
    move_and_rename_files(files_per_category, tgt_dir_path)
    delete_empty_folders(dir_path)
