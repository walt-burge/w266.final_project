import errno
import getopt
import io
from pathlib import Path
import jieba
import logging
import os
import re
from shutil import copyfile
import sys


def preprocess_text_file(input_file, output_file, dict_folder):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # jieba custom setting.
    jieba.set_dictionary(dict_folder + '/dict.txt.big')
    # load stopwords set
    stopwordset = set()
    with io.open(dict_folder + '/stopword.txt','r',encoding='utf-8') as sw:
        for line in sw:
            stopwordset.add(line.strip('\n'))

    texts_num = 0

    output = io.open(output_file, 'w', encoding='utf-8')
    with io.open(input_file,'r', encoding='utf-8') as content:
        for line in content:
            words = jieba.cut(line, cut_all=False)
            for word in words:
                if word not in stopwordset:
                    output.write(word + ' ')

            texts_num += 1
            if texts_num % 10000 == 0:
                logging.info("Processed %d lines" % texts_num)
    output.close() 


def main(argv):

    search_folder_path = ''
    dict_folder_path = ''
    try:
        opts, args = getopt.getopt(argv, "hs:d:z:p", ["spath=", "dpath=",  "z=", "p="])
    except getopt.GetoptError:
        print('test.py -s <src_path> -d <dict_path> -z <seg_file_pattern> [-p <include_file_pattern>]')
        sys.exit(2)

    # Default include_file_pattern to '*'
    include_file_pattern = '.*'
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -s <source_path> -d <dict_path> -z <seg_file_pattern> [-p <include_file_pattern>]')
            sys.exit()
        elif opt in ("-s", "--spath"):
            search_folder_path = arg
        elif opt in ("-d", "--dpath"):
            dict_folder_path = arg
        elif opt in ("-p"):
            include_file_pattern = arg
        elif opt in ("-z"):
            seg_file_pattern = arg
    print('Search for files under {} matching regex "{}", do text segmentation on files matching regex "{}"'.format(
        search_folder_path, include_file_pattern, seg_file_pattern))
    print('Jieba dictionary files under "', dict_folder_path)

    print("Preprocessing Chinese text files under '{}'".format(search_folder_path))

    root_path = str(Path(search_folder_path).absolute().parent)
    folder_name = Path(search_folder_path).name

    result = [os.path.join(dp, f)
                for dp, dn, file_paths in os.walk(search_folder_path)
                    for f in file_paths if ((not f.startswith('.')) and re.match(include_file_pattern, f))]

    for input_file_path in result:
        # Get the sub-path of the input file under root_path+'/'
        input_file_path = input_file_path[len(root_path)+1:]
        # Create a seg file path by replacing the folder_name (e.g. 'cwmt') with folder_name+'.seg'
        seg_file_path = root_path + '/' + input_file_path.replace(folder_name, folder_name+'.seg')
        source_file_path = root_path + '/' + input_file_path
        print("Input: {}, Output: {}".format(source_file_path, seg_file_path))

        if not os.path.exists(os.path.dirname(seg_file_path)):
            try:
                os.makedirs(os.path.dirname(seg_file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        filename = Path(source_file_path).name

        # If this is a Chinese text file, produce a new, segmented version.``
        # Otherwise, just copy it (presumably the rest are the associated English text files.
        #if source_file_path.endswith('_ch.txt') or source_file_path.endswith('_cn.txt'):
            #print("Not this time...")
        if re.match(seg_file_pattern, filename):
            preprocess_text_file(source_file_path, seg_file_path, dict_folder_path)
        else:
            copyfile(source_file_path, seg_file_path)

if __name__ == "__main__":
   main(sys.argv[1:])


