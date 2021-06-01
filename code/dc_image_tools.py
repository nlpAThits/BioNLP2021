import numpy as np
import matplotlib.pyplot as plt
import cv2, os, subprocess, sys
from operator import itemgetter
import ntpath, re, csv, math
from PIL import ImageOps, Image, ImageFilter

np.set_printoptions(threshold=sys.maxsize)

def quick_show(images,title=""):
    fig, ax = plt.subplots(nrows=1, ncols=len(images), squeeze=False)
    for i,img in enumerate(images):
        ax[0][i].imshow(img,  cmap='gray')
        ax[0][i].get_xaxis().set_visible(False)
        ax[0][i].get_yaxis().set_visible(False)
    plt.suptitle(title)
    plt.show()

def warp_image(img, val1=20.0):
    rows, cols = img.shape
    img_output = np.zeros(img.shape, dtype=img.dtype)
    for i in range(rows):
        for j in range(cols):
            # 20.0
            offset_x = int(val1 * math.sin(2 * 3.14 * i / 150))
            offset_y = int(val1 * math.cos(2 * 3.14 * j / 150))
            if i+offset_y < rows and j+offset_x < cols:
                img_output[i,j] = img[(i+offset_y)%rows,(j+offset_x)%cols]
            else:
                img_output[i,j] = 255
    return img_output

def add_salt_and_pepper(image, salt_factor=0.0, salt_strength=255, pepper_factor=0.0, pepper_strength=0):
    output = np.copy(np.array(image))
    nb_salt = np.ceil(output.size * salt_factor)
    coords = [np.random.randint(0, i, int(nb_salt)) for i in output.shape]    
    output[tuple(coords)] = salt_strength

    nb_pepper = np.ceil(output.size * pepper_factor)
    coords = [np.random.randint(0, i, int(nb_pepper)) for i in output.shape]    
    output[tuple(coords)] = pepper_strength

    return Image.fromarray(output)

def latex_to_png(latex_string, char_wrappers, mathfonts, mainfonts, filename, dpi=300, modify=False, header=""):
    result_names=[]
    for fi,f in enumerate(mainfonts):
        for mfi,mf in enumerate(mathfonts):
            for hi,h in enumerate(char_wrappers):        
                closer = ""
                if h!="":
                    closer="}"*int(h[-1])
                    h=h[:-1]
                with open('minilatex.tex','w') as tex_out:
                    #tex_out.write('\\batchmode\n\\documentclass{scrartcl}\n\\thispagestyle{empty}\n\\usepackage{unicode-math}\n\\usepackage{amssymb}\n')
                    tex_out.write('\\batchmode\n\\documentclass{scrartcl}\n\\setlength{\\fboxrule}{0.005pt}\n\\thispagestyle{empty}\n'+ header)#\\usepackage{unicode-math}\n\\usepackage{amssymb}\n')
                    #tex_out.write('\\begin{document}\n{\\fontfamily{'+fn+'}\\selectfont\n'+latex_string+'\n\\end{document}')
                    #tex_out.write('\\setmathfont{'+fn+'}\n\\begin{document}\n'+latex_string+'\n\\end{document}')
                    if mf=="":
                        #tex_out.write('\\begin{document}\n\\fontfamily{'+f+'}\\selectfont\n'+h+latex_string+closer+'\n\\end{document}')
                        tex_out.write('\\begin{document}\n\\fontfamily{'+f+'}\\selectfont\n'+h+"\\fbox{"+latex_string+"}"+closer+'\n\\end{document}')
                    else:
                        tex_out.write('\\begin{document}\n\\fontfamily{'+f+'}\\selectfont\n\\setmathfont{'+mf+'}\n'+h+"\\fbox{"+latex_string+"}"+closer+'\n\\end{document}')
                subprocess.call(['xelatex', 'minilatex.tex'])
                subprocess.call(['pdftocairo', 'minilatex.pdf', '-png', '-singlefile', '-r', str(dpi)])
                img = Image.open('minilatex.png')
                l,t,r,b = ImageOps.invert(img).getbbox()
                border=1
                plain_img = img.crop((l+border,t+border,r-border,b-border))
                w,h=plain_img.size
                # Cut in half
                # img = img.crop((w/2,0,w,h))

#                print("Before", img.size)
#                img = ImageOps.crop(img, border=1)
#                print("After", img.size)
                # Plain, as defined by parameters
                result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+".plain.png")            
                plain_img.save(result_names[-1], "PNG")

                if modify:
                    blurred_img = plain_img.filter(ImageFilter.GaussianBlur(radius=0.75))
                    result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+".blurred.png")
                    blurred_img.save(result_names[-1], "PNG")

#                    blurred2_img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
#                    result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+".blurred2.png")
#                    blurred2_img.save(result_names[-1], "PNG")

                    for sf,ss,pf,ps in [(0.1,255,0,0), (0.25,255,0.0,0), (0,255,0.1,0), (0,255,0.5,180)]:
                        mod_img = add_salt_and_pepper(plain_img, salt_factor=sf, salt_strength=ss, pepper_factor=pf, pepper_strength=ps)                        
                        result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+"."+str(sf)+"_"+str(ss)+"_"+str(pf)+"_"+str(ps)+".plain.png")
                        ImageOps.grayscale(mod_img).save(result_names[-1], "PNG")

                        mod_img = add_salt_and_pepper(blurred_img, salt_factor=sf, salt_strength=ss, pepper_factor=pf, pepper_strength=ps)
                        result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+"."+str(sf)+"_"+str(ss)+"_"+str(pf)+"_"+str(ps)+".blurred.png")
                        ImageOps.grayscale(mod_img).save(result_names[-1], "PNG")

#                        mod_img = add_salt_and_pepper(blurred2_img, salt_factor=sf, salt_strength=ss, pepper_factor=pf, pepper_strength=ps)
#                        result_names.append(filename+"_"+str(fi)+"_"+str(mfi)+"_"+str(hi)+"."+str(sf)+str(ss)+str(pf)+str(ps)+".blurred2.png")
#                        ImageOps.grayscale(mod_img).save(result_names[-1], "PNG")


    return result_names

def analyse_hocr_line_span(line_span):
    line_string = ""        
    stringindex2wordid, wordid2title, wordid2charconfs, wordid2charbboxes, wordid2worstcharconf = {}, {}, {}, {}, {}
    for word_span in [s for s in line_span.descendants if s.name == 'span' and 'ocrx_word' in s['class']]:
        word_text, char_confs, char_bboxes="", "", ""
        worst_char_conf = 100
        for c in [d for d in word_span.descendants if d.name=='span' and 'ocrx_cinfo' in d['class']]:
            assert len(c.text)==1
            # Build up word from single chars
            word_text=word_text+c.text
            # Collect char level confs
            char_conf       =   int(c['title'].split(" ")[-1].split(".")[0])
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

    return line_string, stringindex2wordid, wordid2title, wordid2charconfs, wordid2charbboxes, wordid2worstcharconf

def analyse_hocr_line_span_with_choices(line_span):
    line_string = ""
    stringindex2wordid, wordid2title, wordid2charconfs, wordid2worstcharconf, wordid2glyphcharconfs, wordid2worstglyphcharconf, wordid2charbboxes = {}, {}, {}, {}, {}, {}, {}
    # Go over all words in in line
    for word_span in [s for s in line_span.descendants if s.name == 'span' and 'ocrx_word' in s['class']]:
        word_text, char_confs, char_bboxes="", "", ""
        worst_char_conf = 100
        # Go over all chars in word which have a title (=normal chars w. bboxes)
        for c in [d for d in word_span.descendants if d.name=='span' and 'ocrx_cinfo' in d['class'] and d.has_attr('title')]:
            assert len(c.text)==1
            # Build up word from single chars
            word_text=word_text+c.text
            # Collect char level confs, but with decimals
            #char_conf       =   int(c['title'].split(" ")[-1].split(".")[0])
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
        # Go over all chars in word which have an id (=lstm_choices), skip empty ones directly
        for cs in  [d for d in word_span.descendants if d.name=='span' and 'ocrx_cinfo' in d['class'] and d.has_attr('id')]:
            # We are only interested in the first one, which is the top conf
            choice=list(cs.descendants)[0]
            if choice.text.strip()=="":
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
        #line_string, stringindex2wordid, wordid2title, wordid2charconfs, wordid2charbboxes, wordid2worstcharconf = analyse_hocr_line_span(line_span)
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

#    print("Before (after cleanup)", latex_string)

    for (pat, start_tag, end_tag) in [('^{', '<sup>', '</sup> '), 
                                      ('_{', '<sub>', '</sub>'),
                                      ('\\begin{array}{', '',''),
                                      #('\\begin{equation*}{', '',''),
                                      #('\\begin{equation}{', '','')
                                      ]: # Empty tags mean: remove match
        plen = len(pat)
        while True:
            open_paras=0
            start,end=None, None
            mod=False
            for i in range(len(latex_string)-(plen-1)):
#                print(latex_string[i:i+plen], pat)
                if latex_string[i:i+plen]==pat:
#                    if plen==14: print("PAT", pat)
                    for j in range(i+(plen+1), len(latex_string)):
                        if latex_string[j]=="}":
#                            if plen == 14: print("Close, before", open_paras, j, latex_string[j-3:j+3])
                            if open_paras==0:
                                start=i
                                end=j
                                break
                            else:   open_paras-=1
#                            if plen == 14: print("Close, after", open_paras, j, latex_string[j-3:j+3])
                        elif latex_string[j]=="{":
#                            if plen == 14: print("Open, before", open_paras, j, latex_string[j-3:j+3]) 
                            open_paras+=1
#                            if plen == 14: print("Open, after", open_paras, j, latex_string[j-3:j+3]) 
                    if start and end:
#                        print("Cut from",start,"to", end)
#                        print(latex_string[start:end+1])
                        if start_tag=="" and end_tag=="":
                            latex_string=latex_string[0:start]+latex_string[end+1:]
                        else:
                            latex_string=latex_string[0:start]+start_tag+latex_string[start+plen:end]+end_tag+latex_string[end+(plen-1):]
                            # This works for actual replacements
                            #latex_string=latex_string[0:i]+start_tag+latex_string[i+plen:j]+end_tag+latex_string[j+(plen-1):]
                        mod=True
                        break
            if not mod:
                break
#    print("After", latex_string)
    with open('minilatex.tex','w') as tex_out:
       tex_out.write(latex_string)
    text = subprocess.check_output(["detex", "-l", "-e", "dummy", "minilatex.tex"], encoding='UTF-8').strip()
#    print(text)
    if text != "":  return text
    else:           return None

def pdf_to_pngs(pdf_file, out_dir="./", save_as_base="", dpi=300, force_new=False, verbose=False):
    png_paths=[]
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    out_file_base = save_as_base+ntpath.basename(pdf_file)+"@"+str(dpi)+"DPI-page"
#    newly_created=False
    # Assume whole doc exists if page 01 exists
    if force_new or not os.path.exists(out_dir+"/"+out_file_base+"-01.png"):
        print("\tConverting "+pdf_file+" to "+ str(dpi)+" dpi PNG file ...", file=sys.stderr)
        newly_created=True
        # This will overwrite any existing files of the same name
        subprocess.check_output(["pdftocairo", "-r", str(dpi), "-png", pdf_file, out_dir+"/"+out_file_base])
    else: 
        print("Using existing images ...", file=sys.stderr)        
    for i, png_file in sorted([ (int(a.split("-")[-1].split(".")[0]),  a) for a in os.listdir(out_dir+"/") if a.startswith(out_file_base)], key=itemgetter(0)):
        png_paths.append(new_png_file)

    #         # Create name to which the current pdftocairo output will be renamed.
    #         new_png_file = out_dir+"/"+png_file[:png_file.rfind("-")]+"-"+str(i).zfill(3)+".png"
    #         if os.path.isfile(new_png_file):
    #             print("Removing existing target "+new_png_file, file=sys.stderr)
    #             os.remove(new_png_file)
    #             continue
    #         if new_png_file not in png_paths:
    #             png_paths.append(new_png_file)
    #             if verbose: print("\t\t\t"+png_paths[-1], file=sys.stderr)
    #             os.replace(out_dir+"/"+png_file, png_paths[-1])
    # if not newly_created:
    #     print("Using existing images ...", file=sys.stderr)
    #     for i, png_file in sorted([ (int(a.split("-")[-1].split(".")[0]),  a) for a in os.listdir(out_dir+"/") if a.startswith(out_file_base)], key=itemgetter(0)):
    #         png_paths.append(out_dir+"/"+png_file)
    #         if verbose: print("\t"+png_paths[-1], file=sys.stderr)
    return png_paths

def get_crop_rows(bin_img, max_black_percent=1):
    # Collect contiguous sequences of 'blank' rows in binarized image.
    height, width = bin_img.shape
    blank_row_range, blank_row_ranges=[],[]    
    # Move over bin_img from top to bottom
    for y in range(height):
        if (np.sum(bin_img[y,:])*100)/height <= max_black_percent:
            # The current row counts as 'blank'
            # Add to current range, if that range is contiguous, or to first one
            if len(blank_row_range) == 0 or blank_row_range[-1]==y-1:
                blank_row_range.append(y)
            # A new range starts. End current range, store it, and start new one
            elif len(blank_row_range)!=0:
                blank_row_ranges.append(blank_row_range)
                blank_row_range=[y]
    if len(blank_row_range)!=0:
        # Collect last sep_row_range as well
        blank_row_ranges.append(blank_row_range)
    return blank_row_ranges[0][-1], blank_row_ranges[-1][0]

def chop_image_array(img_array, max_black_percent=1):
    # Binarize and invert so that row and col sum of 0 means completely white
    bin_img = img_array.copy()
    cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU, bin_img)
    height, width = bin_img.shape
    # Move from left to right over binarized word image, looking for sequences 
    # of all-white columns (%sum<=max_black_percent) as vertical char separators
    # Todo: Improve by using histogram thresholding
    sep_col_range, sep_col_ranges=[],[]
    for x in range(width):
        # Max black percentage in a column, consider col as blank if col sum % is lower.
        # Look between crops only
        black_pixels = np.sum(bin_img[:,x])/255
#        print(black_pixels)
        black_percent = (black_pixels/height)*100
#        print(black_percent)
        if  black_percent <= max_black_percent:
            # Current col at x is almost blank
            if len(sep_col_range) == 0 or sep_col_range[-1]==x-1:
                # Add to current range, if contiguous, or to new one
                sep_col_range.append(x)
            elif len(sep_col_range)!=0:
                # End current range. Collect it, if non-empty, and start new one
                sep_col_ranges.append(sep_col_range)
                sep_col_range=[x]
    if len(sep_col_range)!=0:
        # Collect last sep_col_range as well
        sep_col_ranges.append(sep_col_range)

#    print(len(sep_col_ranges))
    split_cols_at=[]
    # Move from sep col to sep col, and collect each col's center value
    for scr_index in range(len(sep_col_ranges)):
        cr      = sep_col_ranges[scr_index]
        # Use center of blank area for split                
        split_cols_at.append(cr[int(len(cr)/2)])

#    print(len(split_cols_at))
    img_chunk_arrays=[]
    start_x=0
    # Go over all split cols and split org image at each
    for end_x in split_cols_at:
        # Collect only if the column is not almost completely empty
        if np.sum(img_array[:,start_x:end_x])>100:
            img_chunk_arrays.append(img_array[:, start_x:end_x].copy())
        start_x=end_x+1
    return img_chunk_arrays


def chop_image_bak(img, show=False, max_black_percent=1, expected_string=""):
    # Binarize and invert so that row and col sum of 0 means completely white
    bin_img = img.copy()
    cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU, bin_img)
    height, width = bin_img.shape

    # Usable area in img goes from top_crop_row to bottom_crop_row 
    top_crop_row, bottom_crop_row = get_crop_rows(bin_img)

    # Move from left to right over binarized word image, looking for sequences 
    # of all-white columns (%sum<=max_black_percent) as vertical char separators
    # Todo: Improve by using histogram thresholding
    sep_col_range, sep_col_ranges=[],[]
    for x in range(width):
        # Max black percentage in a column, consider col as blank if col sum % is lower.
        # Look between crops only
        if (np.sum(bin_img[top_crop_row:bottom_crop_row,x])*100)/height <= max_black_percent: 
            # Current col at x is almost blank
            if len(sep_col_range) == 0 or sep_col_range[-1]==x-1:
                # Add to current range, if contiguous, or to new one
                sep_col_range.append(x)
            elif len(sep_col_range)!=0:
                # End current range. Collect it, if non-empty, and start new one
                sep_col_ranges.append(sep_col_range)
                sep_col_range=[x]
    if len(sep_col_range)!=0:
        # Collect last sep_col_range as well
        sep_col_ranges.append(sep_col_range)

    split_cols_at=[]
    # Move from sep col to sep col, and collect each col's center value
    for scr_index in range(len(sep_col_ranges)):
        cr      = sep_col_ranges[scr_index]
        # Use center of blank area for split                
        split_cols_at.append(cr[int(len(cr)/2)])

    img_chunks=[]
    start_x=0
    # Go over all split cols and split BIN image at each
    for end_x in split_cols_at:
        # Collect only if the column is not almost completely empty
        if np.sum(bin_img[:,start_x:end_x])>100:
            img_chunks.append(img[:, start_x:end_x].copy())
        start_x=end_x+1

    if show and len(img_chunks)>0:
        fig, ax = plt.subplots(nrows=2, ncols=len(img_chunks)+1, squeeze=False)
        for i,im in enumerate(img_chunks):
            ax[0][i].imshow(im,  cmap='gray')    # Works, since no tensor yet
            ax[0][i].get_xaxis().set_visible(False)
            ax[0][i].get_yaxis().set_visible(False)
            if len(expected_string)==len(img_chunks):
                ax[1][i].text(0,0,expected_string[i])
            else:
                ax[1][i].text(0,0,"-")
            ax[1][i].get_xaxis().set_visible(False)
            ax[1][i].get_yaxis().set_visible(False)

        ax[0][i+1].imshow(img,  cmap='gray')    # Works, since no tensor yet
        ax[0][i+1].get_xaxis().set_visible(False)
        ax[0][i+1].get_yaxis().set_visible(False)
        ax[1][i+1].text(0,0,expected_string)
        ax[1][i+1].get_xaxis().set_visible(False)
        ax[1][i+1].get_yaxis().set_visible(False)

        plt.show()        
        plt.close()

    return img_chunks


def overlay_image(img, bboxes, padsize=0, right_offset=0, bottom_offset=0, show=False):
    for l,t,r,b in bboxes:
        img=cv2.rectangle(img, (l-right_offset+padsize,t-bottom_offset+padsize),(r-right_offset+padsize,b-bottom_offset+padsize),(0,0,0),1)
    if show:
        fig, ax = plt.subplots(nrows=1, ncols=1, squeeze=False, figsize=(5,5))
        ax[0][0].imshow(img, cmap='gray')
        ax[0][0].get_xaxis().set_visible(False)
        ax[0][0].get_yaxis().set_visible(False)
        ax[0][0].set_axis_off()
        plt.show()        


def get_roi_array(img, bbox, padsize=20):#, show=False, title="", save_as=None, dpi=300, reduce_height_to_pixels=None, target_width=None):
    # bbox is left, top, right, bottom
    l,t,r,b     = bbox
    # Save org top, left position for returning
    top     = t 
    left    = l
    img_height, img_width   = img.shape
    l = max(0,            l - padsize)
    r = min(img_width,    r + padsize)
    t = max(0,            t - padsize)
    b = min(img_height,   b + padsize)
    roi_array   = np.array(np.array(img)[t:b, l:r])    
#    roi_image   = Image.fromarray(np.array(img)[t:b, l:r])
    return roi_array, top, left


def get_roi(img, bbox, padsize=20, show=False, title="", save_as=None, dpi=300, reduce_height_to_pixels=None, target_width=None):
    # bbox is left, top, right, bottom
    l,t,r,b     = bbox
    # Save org top, left position for returning
    top     = t 
    left    = l
    img_height, img_width   = img.shape
    l = max(0,            l - padsize)
    r = min(img_width,    r + padsize)
    t = max(0,            t - padsize)
    b = min(img_height,   b + padsize)
    roi_array   = np.array(np.array(img)[t:b, l:r])    
    roi_image   = Image.fromarray(np.array(img)[t:b, l:r])

    # Crop away white, such that following resize is based on *content* only (and not in white border)
    temp_img = ImageOps.invert(roi_image)
    imageBox = temp_img.getbbox()
    roi_image=roi_image.crop(imageBox)

    if reduce_height_to_pixels:
        # Use for scaling down the image width proportionally
        factor=reduce_height_to_pixels/(b-t)
        roi_image.thumbnail(((r-l)*factor,reduce_height_to_pixels), Image.ANTIALIAS)

    if target_width:
        roi_image = cv2.copyMakeBorder(np.asarray(roi_image),0,0,0, int(target_width-((r-l)*factor)), cv2.BORDER_CONSTANT, None, 255)
    else:
        roi_image = cv2.copyMakeBorder(np.asarray(roi_image),0,0,0,0, cv2.BORDER_CONSTANT, None, 255)

    if save_as:
        Image.fromarray(roi_image).save(save_as, dpi=(dpi,dpi)) 
    if show:
        roi_image.show()

    return roi_image, top, left


def pad_to_square_and_resize(img, size=(32,32), fill='white', crop_white=False):
    if crop_white:
        # print("Cropping")
        invert_img = ImageOps.invert(img)
        imageBox = invert_img.getbbox()
        cropped=img.crop(imageBox)
        img=cropped

    # We expect img to be smaller or equal to size, not larger
    img_width, img_height   = img.size
    # Find longest side
    pad_to                  = max(img_width, img_height)
    # Either width or height needs to be padded to pad_to
    missing_width           = pad_to - img_width  # Will be 0 if width is the longer side
    missing_height          = pad_to - img_height 
    pad_width               = missing_width // 2
    pad_height              = missing_height // 2    
    padded_img              = ImageOps.expand(img, 
                                (pad_width, pad_height, missing_width - pad_width, missing_height - pad_height), 
                                fill=fill)
    # padded_img is square now, so resizing will not distort it
    return padded_img.resize(size, Image.NEAREST)

