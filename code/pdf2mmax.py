import argparse, pytesseract, os, sys, cv2, subprocess
from bs4 import BeautifulSoup as bs
from dc_image_tools import *    
from pymmax2.pyMMAX2 import * 
from glob import glob

def main(args):
    VERBOSE=False
    if not os.path.exists(args.mmax2_base_path):
        print("MMAX2 base path "+args.mmax2_base_path+" does not exist!", file=sys.stderr)
        return
    in_files=[]
    if os.path.isfile(args.pdf_path):   in_files.append(args.pdf_path)
    else:                               in_files = [f for f in glob(args.pdf_path+"/**", recursive=True) if f.endswith(".pdf")]

    for in_file in in_files:
        mmax2_name = ntpath.basename(in_file).split(".")[0]
        # Create temp common_paths file to get file-level access to MMAX2 data
        cp = MMAX2CommonPaths(args.mmax2_base_path+"common_paths.xml")
        cp.read(verbose=VERBOSE)
        words_filename=args.mmax2_base_path+cp.get_basedata_path()+mmax2_name+"_words.xml"
        if os.path.exists(words_filename):
            print("Basedata exists, removing "+words_filename, file=sys.stderr)
            os.remove(words_filename)
        # Get unexpanded / generic markable file names
        for l in cp.get_markablelevels():
            # Create actual name for checking file existence
            m_file=l.get_filename().replace("$",mmax2_name)
            if os.path.exists(args.mmax2_base_path+cp.get_markable_path()+m_file):
                print("Annotations exist, removing "+args.mmax2_base_path+cp.get_markable_path()+m_file, file=sys.stderr)
                os.remove(args.mmax2_base_path+cp.get_markable_path()+m_file)
        cp = None

        mmax2_proj_name=args.mmax2_base_path+mmax2_name+".mmax"
        with open(mmax2_proj_name,'w') as mmax_out:
            mmax_out.write('<?xml version="1.0" encoding="UTF-8"?>\n<mmax_project>\n<words>'+mmax2_name+'_words.xml</words>\n<keyactions></keyactions>\n<gestures></gestures>\n</mmax_project>')
        mmax2_disc = MMAX2Discourse(mmax2_proj_name, verbose=VERBOSE, mmax2_java_binding=None)
        # Required for init, nothing will be loaded here.
        mmax2_disc.load_markables()

        png_paths = pdf_to_pngs(in_file, out_dir=args.png_base_path, save_as_base="", force_new=args.force_new_png, dpi=args.dpi)
        print(png_paths)
        print(len(png_paths))
        for page_no, png_path in enumerate(png_paths):
            print(page_no)
            # Read as grayscale
            fg_img          = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
            print("\tFile "+png_path, file=sys.stderr)
            print("\t\tOCR ...", file=sys.stderr)
            # Include char-level ocr for confidence values, default values otherwise
            TESS_CONFIG = '--oem 3 --psm 3 -c hocr_char_boxes=1 --dpi '+args.dpi +' --tessdata-dir ' + args.tessdata_dir
            ocr     =   pytesseract.image_to_pdf_or_hocr(fg_img, config=TESS_CONFIG, extension='hocr')
            print("\t\tBS4 ...", file=sys.stderr)
            soup            = bs(ocr, 'html.parser')
            print("\t\thOCR2MMAX2 ...", file=sys.stderr)
            # Add 1 to page no, because image page nos are 1-based
            hocr_to_mmax2(soup, page_no+1, mmax2_disc, ntpath.basename(png_path), verbose=VERBOSE)

        mmax2_disc.get_basedata().write(to_path=mmax2_disc.get_mmax2_path()+mmax2_disc.get_basedata_path(), dtd_base_path='"', overwrite=True)
        mmax2_disc.get_markablelevel('ocr_words').write(to_path=mmax2_disc.get_mmax2_path()+mmax2_disc.get_markable_path(), overwrite=True, no_backup=True)
        mmax2_disc.get_markablelevel('ocr_lines').write(to_path=mmax2_disc.get_mmax2_path()+mmax2_disc.get_markable_path(), overwrite=True, no_backup=True)

if __name__ == '__main__':  
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf_path',           required = True)
    parser.add_argument('--mmax2_base_path',    required = True)
    parser.add_argument('--png_base_path',      required = True)
    parser.add_argument('--tessdata_dir',       required = True)

    parser.add_argument('--dpi',                required = False, default = "300")
    
    parser.add_argument('--force_new_png',      required = False, default = False, dest='force_new_png',   action='store_true')
    parser.add_argument('--force_new_mmax2',    required = False, default = False, dest='force_new_mmax2', action='store_true')

    main(parser.parse_args())

