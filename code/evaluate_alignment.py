import argparse, os, cv2, datetime
#from dc_image_tools import *
#from dc_ml_tools import *
from dc_alignment_tools import *
from pymmax2.pyMMAX2 import *
from glob import glob
# from PIL import Image
import Levenshtein as lev

def main(args):
    eval_outfile = args.eval_outfile if args.eval_outfile !="" else None
    if eval_outfile:
        with open(eval_outfile,"a") as evalout:
            now = datetime.datetime.now()
            evalout.write("\n\n\n*************************\n")
            evalout.write(str(args)+"\n")
            evalout.write(now.strftime("%Y-%m-%d %H:%M:%S\n"))
            evalout.write("*************************\n")

    # For overwriting later
    ocr_mmax2_path = args.ocr_mmax2_path
    xml_mmax2_path = args.xml_mmax2_path
    ocr_in_files, xml_in_files = [],[]

    # Either exactly one .mmax file or a whole folder
    if os.path.isfile(ocr_mmax2_path): 
        ocr_in_files.append(ntpath.basename(ocr_mmax2_path))
        ocr_mmax2_path=os.path.dirname(ocr_mmax2_path)+os.path.sep
    else:   ocr_in_files = [ntpath.basename(f) for f in glob(ocr_mmax2_path+"/**", recursive=True) if f.endswith(".mmax")]
    
    # Either exactly one .mmax file or a whole folder
    if os.path.isfile(xml_mmax2_path): 
        xml_in_files.append(ntpath.basename(xml_mmax2_path))
        xml_mmax2_path=os.path.dirname(xml_mmax2_path)+os.path.sep
    else:   xml_in_files = [ntpath.basename(f) for f in glob(xml_mmax2_path+"/**", recursive=True) if f.endswith(".mmax")]

    # In evaluation, count alignment as correct if both contexts are minimally this similar
    min_norm_lev_sim = float(args.min_context_lev_sim)
    kwic_width=int(args.kwic_width)

    xml_tp_all, xml_fp_all, xml_bd_all = 0,0,0
    n=0
    # Iterate over previously aligned documents
    for (ocr_mmax2_file, xml_mmax2_file) in [(ocr_mmax2_path + os.path.sep + a, xml_mmax2_path + os.path.sep + a) for a in ocr_in_files if a in xml_in_files]:        
        n+=1    # Count all doc pairs
        ocr_disc = MMAX2Discourse(ocr_mmax2_file, verbose=args.verbose, mmax2_java_binding=None)
        ocr_disc.load_markables()
        xml_disc = MMAX2Discourse(xml_mmax2_file, verbose=args.verbose, mmax2_java_binding=None)
        xml_disc.load_markables()
        xml_tp_doc, xml_fp_doc = 0, 0 # Counter for doc_level tp and fp
        # Our main eval dataset is xml, i.e. how many tokens from xml could be correctly mapped to an ocr token
        xml_alignment_markables = xml_disc.get_markablelevel('alignments').get_markables_by_attribute_value('label', args.alignment_label) # alignment markables have span length 1
        # For each aligned bd elem in xml, get the ids of the ocr bd_elements that the bd in xml is aligned with. (target value)
        # These can be one or more!
        # One xml can be aligned to more than one ocr if 
        # - an ocr token was incorrectly split by ocr, and was then corrected by pre_conflate,
        # - by de-hyphenation
        # Get tuples of ocr bd ids (list) and *one* aligned xml_bd_id for all alignments
        for (ocr_bd_ids, xml_bd_id) in [(a.get_attributes()['target'].split("+"), a.get_spanlists()[0][0]) for a in xml_alignment_markables if a.get_attributes().get('target',None)]:
            # Go over all ocr_bd_ids that the current xml is mapped to.
            # Check context for each, but count this xml only *once* as tp or fp
            xml_bd_label=""
            lsep = "  >>  "
            rsep = "  <<  "
            # This is the same for all ocr_bd_ids
            kwic_xml            = kwic_string_for_elements([xml_bd_id], xml_disc.get_basedata(), lsep=lsep, rsep=rsep, strip=True, width=kwic_width, fillwidth=60)
            xml_left_context    = kwic_xml.split(lsep)[0].strip()
            xml_right_context   = kwic_xml.split(rsep)[-1].strip()
            for ocr_bd_id in ocr_bd_ids:
                # ocr_bd_id *must* have *exactly one* alignment markable with xml_bd_id as target
                aligned_xml_bd_id = [a.get_attributes()['target'] for a in ocr_disc.get_markablelevel('alignments').get_markables_for_basedata(ocr_bd_id) if a.get_attributes()['label']==args.alignment_label]
                assert len(aligned_xml_bd_id)   == 1 
                if not xml_bd_id in aligned_xml_bd_id[0].split('+'):
                    print("CRITICAL ERROR!!",xml_mmax2_file)

                # Left and right context must match min sim for *all* ocr ids in order for xml id to count as TP
                # xml_bd_id is the same for all ocr_bd_ids
                kwic_ocr            = kwic_string_for_elements([ocr_bd_id], ocr_disc.get_basedata(), lsep=lsep, rsep=rsep, strip=True, width=kwic_width, fillwidth=60)
                ocr_left_context    = kwic_ocr.split(lsep)[0].strip()
                ocr_right_context   = kwic_ocr.split(rsep)[-1].strip()
                left_sim            = 1-lev.distance(xml_left_context, ocr_left_context) / max(len(xml_left_context), len(ocr_left_context))
                right_sim           = 1-lev.distance(xml_right_context, ocr_right_context) / max(len(xml_right_context), len(ocr_right_context))

                # BOTH context sims must be > 50
                if left_sim>=min_norm_lev_sim and right_sim>=min_norm_lev_sim:
                    # The current xml bd is a tp, and will stay that unless it is overwritten by fp later
                    xml_bd_label="TP"
                else:
                    xml_bd_label="FP"
                    # If one ocr bd does not match, the entire xml bd does not match, so stop searching and comparing
                    break
                # Move on to next ocr_id
            # all ocr_bd_ids have been checked, or label is fp
            if args.verbose:
                print("\n\n"+xml_bd_label+"\t"+str(left_sim)+"\t"+str(right_sim))
                print(kwic_xml)
                print(kwic_ocr)
            if xml_bd_label     == "TP":
                xml_tp_doc+=1
                xml_tp_all+=1
            elif xml_bd_label   == "FP":
                xml_fp_doc+=1
                xml_fp_all+=1
            # go on to next mapped xml_bd_id

        # all xml bds in current file have been processed
        # Collect total number of xml bds
        xml_bd_all+=xml_disc.get_bd_count()
#        print("BD in xml ",xml_disc.get_bd_count())
        # Compute p for current pair
        p_xml   =   xml_tp_doc/(xml_tp_doc+xml_fp_doc)  # Correctly found / all found
        r_xml   =   xml_tp_doc/xml_disc.get_bd_count()  # Correctly found / all correct. Note: This assumes that all elements in xml can actually be mapped.
        try:                        f_xml   = (2*p_xml*r_xml) / (p_xml+r_xml)
        except ZeroDivisionError:   f_xml   = 0
        if eval_outfile:
            with open(eval_outfile,"a") as evalout:
                evalout.write("\n"+ocr_disc.info(mono=True))
                evalout.write(xml_disc.info(mono=True))
                evalout.write(args.alignment_label+": P, R, F: "+ str(p_xml)+ "\t"+ str(r_xml)+"\t"+ str(f_xml)+"\n")
        print(args.alignment_label+": P, R, F: "+ str(p_xml)+ "\t"+ str(r_xml)+"\t"+ str(f_xml)+"\n")

    # all pairs have been processed
    p_xml   =   xml_tp_all/(xml_tp_all+xml_fp_all) # Correctly found / all found
    r_xml   =   xml_tp_all/xml_bd_all # Correctly found / all correct. Note: This assumes that all elements in xml can actually be mapped.
    f_xml   =   (2*p_xml*r_xml) / (p_xml+r_xml)
    if eval_outfile:
        with open(eval_outfile,"a") as evalout:
            evalout.write(args.alignment_label+": P, R, F (micro): "+ str(p_xml)+ "\t"+ str(r_xml)+"\t"+ str(f_xml)+" n = "+str(n)+"\n")
    print(args.alignment_label+": P, R, F (micro): "+ str(p_xml)+ "\t"+ str(r_xml)+"\t"+ str(f_xml)+" n = "+str(n)+"\n")

if __name__ == '__main__':  
    parser = argparse.ArgumentParser()
    parser.add_argument('--ocr_mmax2_path',         required = True) 
    parser.add_argument('--xml_mmax2_path',         required = True) 
    parser.add_argument('--verbose',                dest='verbose',         action='store_true',    default=False)
    # Evaluate alignments with this label only
    parser.add_argument('--alignment_label',        required = True)
    parser.add_argument('--kwic_width',             required = False, default='15')
    parser.add_argument('--min_context_lev_sim',    required = False, default='0.5')
    parser.add_argument('--eval_outfile',           required = False, default = "eval_out.txt")

    main(parser.parse_args())






        # # alignments are always markables with *exactly* one bd element
        # ocr_alignment_markables = ocr_disc.get_markablelevel('alignments').get_markables_by_attribute_value('label', args.alignment_label)
        # # For each aligned bd elem in ocr, get the ids of the xml bd_elements that the bd in ocr is aligned with. (target value)
        # # These can be one or more!
        # # One ocr can be aligned to more than one xml if 
        # # - an ocr token was incorrectly merged by ocr, and was then corrected by pre_split.
        # for (xml_targets, ocr_bd) in [(a.get_attributes()['target'].split("+"),a.get_spanlists()[0][0]) for a in ocr_alignment_markables if a.get_attributes().get('target',None)]:
        #     rel_string="ocr-1-to-"+str(len(xml_targets))+"-xml"

        #     for xml_target in xml_targets:
        #         # ocr_bd is the same for all xml_targets
        #         print("\n"+rel_string+"\tOCR"+kwic_string_for_elements([ocr_bd],     ocr_disc.get_basedata(), lsep="_>>   ", rsep="   <<_", strip=True, width=10))
        #         print(     rel_string+"\tXML"+kwic_string_for_elements([xml_target], xml_disc.get_basedata(), lsep="_>>   ", rsep="   <<_", strip=True, width=10))
           
