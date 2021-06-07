import argparse, os, sys, re
from bs4 import BeautifulSoup as bs
from pymmax2.pyMMAX2 import *
from glob import glob
from dc_image_tools import *

#def parse_recursively(content_in, open_tags, pad_from_last_cont, mmax2_disc, styles, de_tex=False):
def parse_recursively(content_in, open_tags, pad_from_last, mmax2_disc, styles, de_tex=False):
#    print(pad_from_last_cont)
    # Go over all *top-level* content elements included in content incl. tags and text. style_atts will be None for tl regions
    # Content in these tags will be imported
    struct_tags =   ['title', 'surname', 'given-names', 'email', 'p', 'sec', 'xref', 'tr', 'td', 'caption', 'label', 'rendered-tex-math']
    # These tags are converted into typography-info for the MMAX2 data
    format_tags =   ['italic', 'sup', 'sub', 'underline', 'bold']
    for content in content_in.children:
#        print(content.name)
        if content.name and (content.name in struct_tags or content.name in format_tags):
            # Normalize typography-related tags to 'span'
            if content.name in format_tags: cname='span'        
            else:                           cname=content.name
            if cname=='span':               styles.append(content.name)
            open_tags.append((cname, None, None, styles))
            # Store tag list pos
            list_pos=len(open_tags)-1
            # Parse its contents recursively
#            parse_recursively(content, open_tags, pad_from_last_cont, mmax2_disc, styles, de_tex=de_tex)
            parse_recursively(content, open_tags, pad_from_last, mmax2_disc, styles, de_tex=de_tex)
            # Get tag, and overwrite end with last bd element id
            (_, b_start, b_end, styles) = open_tags[list_pos]
            open_tags[list_pos]=(cname, b_start, mmax2_disc.get_basedata().get_elements()[-1][1], styles.copy())
            if cname=='span': styles.pop()
        elif de_tex and content.name == 'tex-math':
            tex_rendered=latex_to_text(content.get_text())
            if tex_rendered:
                # parse again because de_tex will probably have added some tags like <sup>, <sub>, etc.
#                parse_recursively(bs('<rendered-tex-math>'+tex_rendered+'</rendered-tex-math>', 'html.parser'), open_tags, pad_from_last_cont, mmax2_disc, styles, de_tex=de_tex)
                parse_recursively(bs('<rendered-tex-math>'+tex_rendered+'</rendered-tex-math>', 'html.parser'), open_tags, pad_from_last, mmax2_disc, styles, de_tex=de_tex)
        elif not content.name:
            # Allow for absolute padding using more than one space            
            # Apply pad_from_last to the left of the current content
            content=pad_from_last[0]+content
            new_pad_len=len(content)-len(content.rstrip())
#            print(new_pad_len)
#            content=content.rstrip()
            pad_from_last[0] = new_pad_len * " "

#            if pad_from_last_cont[0]:   content=" "+content
 #           if content.endswith(" "):   pad_from_last_cont[0]=True
  #          else:                       pad_from_last_cont[0]=False

            # The content is text. The first elem of this text is the start of all currently open tags w/o any start.           
            span=mmax2_disc.add_basedata_elements_from_string(content)
            if len(span)>0:
                for p, (b_name, b_start, b_end, b_styles) in enumerate(open_tags):
                    if not b_start: open_tags[p]=(b_name, span[0], b_end, b_styles)
        else:
            # Current elem is a tag that we want to ignore. It might have some interesting children, though, so recurse into it.
#            parse_recursively(content, open_tags, pad_from_last_cont, mmax2_disc, styles, de_tex=de_tex)
            parse_recursively(content, open_tags, pad_from_last, mmax2_disc, styles, de_tex=de_tex)



def main(args):
    VERBOSE=False
    if not os.path.exists(args.mmax2_base_path):
        print("MMAX2 base path "+args.mmax2_base_path+" does not exist!", file=sys.stderr)
        return

    in_files=[]

    if os.path.isfile(args.pmc_path):
        in_files.append(args.pmc_path)
    else:
        in_files = [f for f in glob(args.pmc_path+"/**", recursive=True) if f.endswith(".nxml")]

    for in_file in in_files:
        #mmax2_name = ntpath.basename(args.pmc_path).split(".")[0]
        mmax2_name = ntpath.basename(in_file)[0:ntpath.basename(in_file).rfind('.')].replace('.LOCAL','')
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

        # Read full nxml at once
        with open(in_file, 'r') as f_in: contents = f_in.read()

        # Skip if PMC doc is not open access (will not contain full text)
        if "<?properties open_access?>" not in contents:
            print(in_file+" is not open access!")
            sys.exit()
        # Make .nxml readable for bs4
        if "<html><body>" in contents:  
            contents=contents.replace("<html><body>","").replace("</body></html>","")   # Remove any <html>-body
        if "<body>" not in contents:    
            contents=contents.replace("</front>","</front>\n<body>").replace("<back>","</body>\n<back>")    # Add content body tag, if not present

        # Add space between label and labelee
        contents=contents.replace('</label>','</label>  ')

        if args.nice_tables:
            # Fix table markup to include space between cells 
            contents=contents.replace('<tr>'  , '     <tr>')    # Before row
            contents=contents.replace('</tr>' , '</tr> ')       # After row

            contents=contents.replace('<td'   , '     <td')     # Before each cell in row
            contents=contents.replace('</td>'   , '</td> ')     # After each cell in row

            contents=contents.replace('<th'   , '     <th')     # Before each th
            contents=contents.replace('</th>'   , '</th> ')     # After each th

        if args.nice_names:
            contents=contents.replace('</given-names></name>','</given-names>     </name>')

        soup = bs(contents, 'html.parser')

        was_added, lm = mmax2_disc.get_markablelevel("structure").add_markable([mmax2_disc.add_basedata_elements_from_string(soup.find('article-title').text)], apply_default=True)
        if was_added:   
            lm.update_attributes({'type':'pub-title'})
        # Store tag-name, start_id, end_id, attributes
        open_tags=[]
        # Only import abstract and body content, and contributors and affiliation
        for region_name in ['contrib-group', 'aff', 'abstract', 'body']:
            # Get all tags of type region, incl. all descendants
            for region in soup.find_all(region_name, recursive=True):
                # A tag of type region starts. Note: There can be more than one abstract!
                open_tags.append((region_name, None, None, None)) # No need to store atts.
                # Remember at which pos the current tag is stored
                list_pos=len(open_tags)-1
                # Parse full region recursively, no padding, no style attributes since this is the top-level
                #pad_from_last=False
                pad_from_last=""
                parse_recursively(region, open_tags, [pad_from_last], mmax2_disc, [], de_tex=args.de_tex)
                # Now we know where the current region ends
                (_, b_start, b_end, _) = open_tags[list_pos]
                open_tags[list_pos]=(region_name, b_start, mmax2_disc.get_basedata().get_elements()[-1][1], None)

        # Now condense attributes of identical spans from bottom to top
        last_start, last_end = -1, -1
        last_type=""
        to_del=[]
        # Go over all tags backwards
        for r_index in range(len(open_tags)-1,0,-1):
            # Get current tag
            (b_type, b_start, b_end, styles) = open_tags[r_index]
            # Only if current tag and last seen is span
    #       if b_type=='span' and last_type=='span':
            if b_type == last_type:
                if b_start == last_start and b_end == last_end:
                    new_styles=styles.copy()
                    new_styles.extend(open_tags[r_index+1][3])
                    open_tags[r_index]=(b_type,b_start,b_end,list(set(new_styles)))
                    # Mark as to be deleted later
                    to_del.append(r_index+1)
            last_start  =   b_start
            last_end    =   b_end
            last_type   =   b_type
        # to_del is backwards due to how it was created, so deleting forward is index-safe
        for td in to_del:
            del open_tags[td]

        # Write basedata
        mmax2_disc.get_basedata().write(to_path=mmax2_disc.get_mmax2_path()+mmax2_disc.get_basedata_path(), dtd_base_path='"', overwrite=True)

        # Create structure markables
        for (b_type, b_start, b_end, styles) in open_tags:
            if b_type not in ['contrib-group']:
                if b_start and b_end:
                    was_added, m = mmax2_disc.get_markablelevel("structure").add_markable(spanlists=span_to_spanlists(b_start+".."+b_end, mmax2_disc.get_basedata()), 
                                                allow_duplicate_spans=True, apply_default=True)
                    if was_added:
                        atts={'type':b_type}
                        if styles:
                            for i in styles:
                                atts[i]='true'
                        m.update_attributes(atts)

        mmax2_disc.get_markablelevel('structure').write(to_path=mmax2_disc.get_mmax2_path()+mmax2_disc.get_markable_path(), overwrite=True, no_backup=True)
        print(mmax2_disc.info())

if __name__ == '__main__':  
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--pmc_path',           required = True)
    parser.add_argument('--mmax2_base_path',    required = True)
    parser.add_argument('--de_tex',             required = False, default = False, dest='de_tex',  action='store_true')

    parser.add_argument('--nice_names',         required = False, default = False, dest='nice_names',  action='store_true')
    parser.add_argument('--nice_tables',        required = False, default = False, dest='nice_tables',  action='store_true')


    main(parser.parse_args())

