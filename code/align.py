import argparse, datetime
from dc_alignment_tools import *
from pymmax2.pyMMAX2 import *
import numpy as np
from glob import glob
from os import path
from collections import Counter

def main(args):
    ocr_mmax2_path                                  = args.ocr_mmax2_path
    xml_mmax2_path                                  = args.xml_mmax2_path
    ocr_in_files, xml_in_files                      = [],[]

    # Check for bulk processing
    if os.path.isfile(ocr_mmax2_path): 
        ocr_in_files.append(ntpath.basename(ocr_mmax2_path))
        ocr_mmax2_path=path.dirname(ocr_mmax2_path)+os.path.sep
    else:   
        ocr_in_files = [ntpath.basename(f) for f in glob(ocr_mmax2_path+"/**", recursive=True) if f.endswith(".mmax")]

    if os.path.isfile(xml_mmax2_path): 
        xml_in_files.append(ntpath.basename(xml_mmax2_path))
        xml_mmax2_path=path.dirname(xml_mmax2_path)+os.path.sep
    else:   
        xml_in_files = [ntpath.basename(f) for f in glob(xml_mmax2_path+"/**", recursive=True) if f.endswith(".mmax")]

    all_forced_alignments=[Counter()]

    # Get tuples of matching .mmax files
    for (ocr_mmax2_file, xml_mmax2_file) in \
                [(ocr_mmax2_path + os.path.sep + a, xml_mmax2_path + os.path.sep + a) for a in ocr_in_files if a in xml_in_files]:
        ocr_disc = MMAX2Discourse(ocr_mmax2_file, verbose=args.verbose, mmax2_java_binding=None)
        ocr_disc.load_markables()
        # Delete existing alignment markables with label == args.alignment_label
        print("Retrieving alignment markables with label '"+args.alignment_label+"' ...", file=sys.stderr)
        to_del=ocr_disc.get_markablelevel('alignments').get_markables_by_attribute_value('label',args.alignment_label)
        if len(to_del)>0:
            print("Removing "+str(len(to_del))+" markables ...", file=sys.stderr)
            for t in to_del:
                t.delete()
            print("Done!", file=sys.stderr)
            # Save 
            ocr_disc.get_markablelevel("alignments").write(to_path=ocr_disc.get_mmax2_path()+ocr_disc.get_markable_path(), overwrite=True, no_backup=True)
        ocr_str, all_ocr_words, all_ocr_ids, _ = ocr_disc.render_string()

        xml_disc = MMAX2Discourse(xml_mmax2_file, verbose=args.verbose, mmax2_java_binding=None)
        xml_disc.load_markables()
        # See above. 
        print("Retrieving alignment markables with label '"+args.alignment_label+"' ...", file=sys.stderr)
        to_del=xml_disc.get_markablelevel('alignments').get_markables_by_attribute_value('label',args.alignment_label)
        if len(to_del)>0:
            print("Removing "+str(len(to_del))+" markables ...", file=sys.stderr)
            for t in to_del:
                t.delete()
            print("Done!", file=sys.stderr)
            # Save 
            xml_disc.get_markablelevel("alignments").write(to_path=xml_disc.get_mmax2_path()+xml_disc.get_markable_path(), overwrite=True, no_backup=True)

        if args.dry_run:    continue
        # Get xml version as reference
        xml_str, all_xml_words, all_xml_ids, _ = xml_disc.render_string()

        if True: #not a
            if int(args.pre_comp_size)>0:
                # No effect on alignment quality 
                all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids = \
                    compress(all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids, 
                        int(args.pre_comp_size), recursive=args.pre_comp_recursive, verbose=args.verbose)
            if args.de_hyphenate:
                # Positive effect on quality 
                all_ocr_words, all_ocr_ids = \
                    conflate_hyphenated_ocr_splits(all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids, 
                        fold=True, verbose=args.verbose)
            if args.pre_conflate:
                all_ocr_words, all_ocr_ids = \
                    conflate_exact_ocr_splits(all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids, 
                        recursive=True, verbose=args.verbose)
            if args.pre_split:        
                all_ocr_words, all_ocr_ids = \
                    split_exact_ocr_conflations(all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids, 
                        recursive=True, verbose=args.verbose)

            ocr_words_al, ocr_ids_al, xml_words_al, xml_ids_al = \
                align_tokens(all_ocr_words, all_ocr_ids, all_xml_words, all_xml_ids, gap_char="<<GAP>>", method=args.alignment_type)
                                                                          
            if args.post_forcealign:
                ocr_words_al, ocr_ids_al, xml_words_al, xml_ids_al = forcealign_tokens(ocr_words_al, ocr_ids_al, xml_words_al, xml_ids_al,
                                                                                                          all_forced_alignments, dynamic=True, 
                                                                                                          recursive=args.post_forcealign_recursive, 
                                                                                                          gap_char="<<GAP>>", verbose=args.verbose)

            if args.verbose:
                for f in all_forced_alignments[0]:
                    print(f, all_forced_alignments[0][f])

            # Both lists should have the same length now
            check_alignment(ocr_words_al, xml_words_al, ocr_ids_al, xml_ids_al)
            ocr2pmc=create_id_to_id_mapping(ocr_words_al, xml_words_al, ocr_ids_al, xml_ids_al)

            # Mapping dict done
            # Create alignments & eval
            for ocr_id in ocr2pmc.keys():
                # ocr_id is always atomic
                # xml_ids might be +-separated list
                xml_id_string = ocr2pmc[ocr_id]

                m_done=False
                # We now distinguish different alignments by 'label'. First check if markable FOR THE CURRENT LABEL exists for ocr_id already.
                for k in ocr_disc.get_markablelevel("alignments").get_markables_for_basedata(ocr_id):
                    if k.get_attributes().get('label','')==args.alignment_label:
                        # Update this markable
                        k.update_attributes({'target':k.get_attributes()['target']+"+"+xml_id_string})
                        m_done=True
                        break
                if not m_done:
                    # OCR --> PMC. Create markable on OCR level. 
                    new_m, m = ocr_disc.get_markablelevel("alignments").add_markable(spanlists=[[ocr_id]], allow_duplicate_spans=True, apply_default=True)
                    # Now, no markable can exist here
                    assert new_m            
                    m.update_attributes({'target':xml_id_string, 'label':args.alignment_label, 'validated':'u'})

                # XML --> OCR. Create markable on XML level.
                # A markable might exist there already 
                for xml_id in xml_id_string.split("+"):
                    m_done=False
                    # We now distinguish different alignments by 'label'. First check if markable FOR THE CURRENT LABEL exists for xml_id already.
                    for k in xml_disc.get_markablelevel("alignments").get_markables_for_basedata(xml_id):
                        if k.get_attributes().get('label','')==args.alignment_label:
                            k.update_attributes({'target':k.get_attributes()['target']+"+"+ocr_id})    
                            m_done=True
                            break
                    if not m_done:                    
                        new_m, m = xml_disc.get_markablelevel("alignments").add_markable(spanlists=[[xml_id]], allow_duplicate_spans=True, apply_default=True)
                        assert new_m
                        #if new_m:   
                        m.update_attributes({'target':ocr_id, 'label':args.alignment_label, 'validated':'u'})

            xml_disc.get_markablelevel("alignments").write(to_path=xml_disc.get_mmax2_path()+xml_disc.get_markable_path(), overwrite=True, no_backup=True)
            ocr_disc.get_markablelevel("alignments").write(to_path=ocr_disc.get_mmax2_path()+ocr_disc.get_markable_path(), overwrite=True, no_backup=True)        

if __name__ == '__main__':  
    parser = argparse.ArgumentParser(allow_abbrev=False)
    # Files to be aligned must have the same name (but come from different folders.)
    # Path to file containing previously MMAX2-converted OCR files (named PMCXXXXXXX.mmax), or exactly one such file.
    parser.add_argument('--ocr_mmax2_path',     required = True) 
    # Path to file containing previously MMAX2-converted PMC files (named PMCXXXXXXX.mmax), or exactly one such file.    
    parser.add_argument('--xml_mmax2_path',     required = True) 

    # Label to be assigned to alignment markables created by this alignment 
    parser.add_argument('--alignment_label',    required = True)

    # Join words that are hyphenated in OCR version prior to alignment. 
    parser.add_argument('--de_hyphenate',       dest='de_hyphenate',    action='store_true',    default=False)
    # Join (=conflate) tokens that are incorrectly split in OCR version prior to alignment.
    parser.add_argument('--pre_conflate',       dest='pre_conflate',    action='store_true',    default=False)
    # Split tokens that are incorrectly merged in OCR prior to alignment
    parser.add_argument('--pre_split',          dest='pre_split',       action='store_true',    default=False)

    # Compress trivial matches in OCR and PMC in order to help subsequent alignmend and reduce no. of tokens to align
    parser.add_argument('--pre_comp_size',      default="20")
    parser.add_argument('--pre_comp_recursive', dest='pre_comp_recursive',   action='store_true', default=False)

    # local or global. To be passed on to select either Bio.pairwise2.align.localxx or Bio.pairwise2.align.globalxx in alignment.
    # global seems to yield slightly lower recall but apparently better precision (not quantified)
    parser.add_argument('--alignment_type', default = "global")

    # Apply some heuristics to align remaining unaligned tokens after alignment. Recursive is always false by default
    parser.add_argument('--post_forcealign',                dest='post_forcealign', action='store_true',                default=False)
    parser.add_argument('--post_forcealign_recursive',      dest='post_forcealign_recursive', action='store_true',      default=False)

    parser.add_argument('--verbose',                        dest='verbose',         action='store_true',    default=False)
    parser.add_argument('--dry_run',            dest='dry_run',         action='store_true',    default=False)

    main(parser.parse_args())


