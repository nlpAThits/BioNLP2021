import numpy as np
import matplotlib.pyplot as plt
import cv2, os, subprocess, sys
from operator import itemgetter
import ntpath, re, csv, math
from PIL import ImageOps, Image, ImageFilter

np.set_printoptions(threshold=sys.maxsize)

def analyse_hocr_line_span_with_choices(line_span):
    line_string = ""
    stringindex2wordid, wordid2title, wordid2charconfs, wordid2worstcharconf, wordid2glyphcharconfs, wordid2worstglyphcharconf, wordid2charbboxes = {}, {}, {}, {}, {}, {}, {}
    # Go over all words in line
    for word_span in [s for s in line_span.descendants if s.name == 'span' and 'ocrx_word' in s['class']]:

        word_text, char_confs, char_bboxes = "", "", ""
        worst_char_conf = 100
        # Go over all chars in word which have a title (=normal chars w. bboxes)
        for c in [d for d in word_span.descendants if d.name=='span' and 'ocrx_cinfo' in d['class'] and d.has_attr('title')]:
            assert len(c.text)==1
            # Build up word from single chars
            word_text=word_text+c.text
            # Collect char level confs, but with decimals
            char_conf       =   float(c['title'].split(" ")[-1])
            if char_conf < worst_char_conf:
                worst_char_conf=char_conf
            char_confs      =   char_confs  + str(char_conf)+","
            char_bboxes     =   char_bboxes + c['title'].split(";")[0][9:]+","

        # word has been built up
        wordid2charconfs[word_span['id']]               = char_confs[0:-1]  # Cut off last comma
        wordid2charbboxes[word_span['id']]              = char_bboxes[0:-1]  # Cut off last comma
        wordid2worstcharconf[word_span['id']]           = str(worst_char_conf)
        for i in range(len(word_text)):
            # Map org string pos to word_id
            stringindex2wordid[len(line_string)+i+1]    = word_span['id']  # Add one for leading space
            wordid2title[word_span['id']]               = word_span['title']
        # Build line rep with standard space-based separators, to be used as input to add_elements_from_string method
        line_string=line_string+" "+word_text

        glyph_char_confs=""
        worst_glyph_char_conf = 100
        for cs in  [d for d in word_span.descendants if d.name=='span' and 'ocrx_cinfo' in d['class'] and d.has_attr('id')]:
            # We are only interested in the first one, which is the top conf
#            print("\n"+str(cs))
            try:
                choice=list(cs.descendants)[0]
            except IndexError:
                print("No glyph info 1, please check your tesseract version!", file=sys.stderr)
                continue
            if choice.text.strip()=="":
                print("No glyph info 2, please check your tesseract version!", file=sys.stderr)
                continue
            glyph_char_conf       =   int(choice['title'].split(" ")[-1])
            if glyph_char_conf < worst_glyph_char_conf:
                worst_glyph_char_conf=glyph_char_conf
            glyph_char_confs      =   glyph_char_confs  + str(glyph_char_conf)+","

        wordid2glyphcharconfs[word_span['id']]               = glyph_char_confs[0:-1]  # Cut off last comma
        wordid2worstglyphcharconf[word_span['id']]           = str(worst_glyph_char_conf)

    return line_string, stringindex2wordid, wordid2title, wordid2charconfs, wordid2worstcharconf, wordid2glyphcharconfs, wordid2worstglyphcharconf, wordid2charbboxes

# With char-level output and lstm_choices
def hocr_to_mmax2(hocr_soup, page_no, mmax2_discourse, img_name, verbose=False):
    # Go over all spans of class 'ocr_line'. Each has the line words as its children.
    if verbose: print(hocr_soup)
    for line_span in [s for s in hocr_soup.descendants if s.name == 'span' and 'ocr_line' in s['class']]:
        line_string,stringindex2wordid,wordid2title,wordid2charconfs,wordid2worstcharconf,wordid2glyphcharconfs,wordid2worstglyphcharconf,wordid2charbboxes=\
                analyse_hocr_line_span_with_choices(line_span)
        if line_string.strip() == "":   continue

        # Line has been built up. Now create bd elements ...
        line_bd_ids = mmax2_discourse.get_basedata().add_elements_from_string(line_string)        
        # ... and re-render line.
        rendered, _, _, mapping = mmax2_discourse.get_basedata().render_string(for_ids=[line_bd_ids], mapping=True)
        last_id = None
        current_ocr_span=[] # Collect (index, id) tuples of spans mapped to the same ocr word
        current_bd_span=[]
        # Go over all positions in ocr string
        for i in sorted(stringindex2wordid.keys()):
            if last_id and stringindex2wordid[i] != last_id:
                # Current span ends. Collect bd_ids mapped to this ocr_word, in case an ocr token yielded more than one bd element.
                for (j,_) in current_ocr_span:
                    try:
                        # Store each bd_id only once
                        if mapping[j] not in current_bd_span:   current_bd_span.append(mapping[j])
                    except KeyError:    pass
                # Add ocr_word markable
                was_added, m = mmax2_discourse.get_markablelevel("ocr_words").add_markable([current_bd_span], allow_duplicate_spans=False)
                assert was_added
                # Set attribute to ocr word. There is a 1-to-1 mapping between ocr_word markables and title attributes
                # bbox 588 827 622 837; x_wconf 96
                # Use attributes from last_id word
                bbox=wordid2title[last_id].split(";")[0][5:]
                conf=wordid2title[last_id].split(";")[1][9:]
                m.update_attributes({'word_bbox':bbox,
                                     'word_conf':str(conf),
                                     'char_confs':wordid2charconfs[last_id],
                                     'worst_char_conf':wordid2worstcharconf[last_id], 
                                     'glyph_char_confs':wordid2glyphcharconfs[last_id],
                                     'worst_glyph_char_conf':wordid2worstglyphcharconf[last_id], 
                                     'char_bboxes':wordid2charbboxes[last_id],                                      
                                     'image':img_name, 
                                     'page_no':str(page_no)})
                current_ocr_span=[]
                current_bd_span=[]
            # Collect in current ocr span
            current_ocr_span.append((i,stringindex2wordid[i]))
            last_id = stringindex2wordid[i]

        # All string positions in line_span have been processed
        # Create markable for last pending ocr_span
        for (j,_) in current_ocr_span:
            try:
                if mapping[j] not in current_bd_span:
                    current_bd_span.append(mapping[j])
            except KeyError:
                pass
        was_added, m = mmax2_discourse.get_markablelevel("ocr_words").add_markable([current_bd_span], allow_duplicate_spans=False)
        assert was_added
        # Here, use atts from current id (last val of i)
        bbox=wordid2title[stringindex2wordid[i]].split(";")[0][5:]
        conf=wordid2title[stringindex2wordid[i]].split(";")[1][9:]            
        m.update_attributes({'word_bbox':bbox,
                             'word_conf':str(conf),
                             'char_confs':wordid2charconfs[stringindex2wordid[i]],
                             'worst_char_conf':wordid2worstcharconf[stringindex2wordid[i]], 
                             'glyph_char_confs':wordid2glyphcharconfs[stringindex2wordid[i]],
                             'worst_glyph_char_conf':wordid2worstglyphcharconf[stringindex2wordid[i]], 
                             'char_bboxes':wordid2charbboxes[stringindex2wordid[i]], 
                             'image':img_name, 
                             'page_no':str(page_no)})

        was_added, m = mmax2_discourse.get_markablelevel("ocr_lines").add_markable([line_bd_ids], allow_duplicate_spans=False)
        assert was_added
        bbox=line_span['title'].split(";")[0][5:]
        m.update_attributes({'line_bbox':bbox , 'image':img_name, 'page_no':str(page_no)})
    return

def latex_to_text(latex_string, cleanup=True):
    print("De-texing tex-math...", file=sys.stderr)
    if cleanup:
        # Add some more
        latex_string=latex_string.replace('\\cdot',  '·')
        latex_string=latex_string.replace('\\\\',    ' ')
        latex_string=latex_string.replace('\n',      ' ',)
        latex_string=latex_string.replace('^{}',     '')
        latex_string=latex_string.replace('_{}',     '')
        latex_string=latex_string.replace('{}',     '')
        latex_string=latex_string.replace('\\begin{equation*}',     '')
        latex_string=latex_string.replace('\\begin{equation}',     '')
        latex_string=latex_string.replace('\\end{equation*}',     '')
        latex_string=latex_string.replace('\\end{equation}',     '')
        latex_string=latex_string.replace('^{ ',     '^{')
        latex_string=latex_string.replace('_{ ',     '_{')

    for (pat, start_tag, end_tag) in [('^{', '<sup>', '</sup> '), 
                                      ('_{', '<sub>', '</sub>'),
                                      ('\\begin{array}{', '',''),
                                      ]: # Empty tags mean: remove match
        plen = len(pat)
        while True:
            open_paras=0
            start,end=None, None
            mod=False
            for i in range(len(latex_string)-(plen-1)):
                if latex_string[i:i+plen]==pat:
                    for j in range(i+(plen+1), len(latex_string)):
                        if latex_string[j]=="}":
                            if open_paras==0:
                                start=i
                                end=j
                                break
                            else:   open_paras-=1
                        elif latex_string[j]=="{":
                            open_paras+=1
                    if start and end:
                        if start_tag=="" and end_tag=="":
                            latex_string=latex_string[0:start]+latex_string[end+1:]
                        else:
                            latex_string=latex_string[0:start]+start_tag+latex_string[start+plen:end]+end_tag+latex_string[end+(plen-1):]
                            # This works for actual replacements
                        mod=True
                        break
            if not mod:
                break
    with open('minilatex.tex','w') as tex_out:
       tex_out.write(latex_string)
    text = subprocess.check_output(["detex", "-l", "-e", "dummy", "minilatex.tex"], encoding='UTF-8').strip()
    if text != "":  return text
    else:           return None

def pdf_to_pngs(pdf_file, out_dir="./", save_as_base="", dpi=300, force_new=False, verbose=False):
    png_paths=[]
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    out_file_base = save_as_base+ntpath.basename(pdf_file)+"@"+str(dpi)+"DPI-page"
    # Assume whole doc exists if page 01 exists
    if force_new or not os.path.exists(out_dir+"/"+out_file_base+"-01.png"):
        print("\tConverting "+pdf_file+" to "+ str(dpi)+" dpi PNG file ...", file=sys.stderr)
        # This will overwrite any existing files of the same name
        subprocess.check_output(["pdftocairo", "-r", str(dpi), "-png", pdf_file, out_dir+"/"+out_file_base])
    else: 
        print("Using existing images ...", file=sys.stderr)        
    return [ u[1] for u in sorted([ (int(a.split("-")[-1].split(".")[0]),  out_dir+"/"+a) for a in os.listdir(out_dir+"/") if a.startswith(out_file_base)], key=itemgetter(0))]
