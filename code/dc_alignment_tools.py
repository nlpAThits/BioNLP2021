import sys
from Bio import pairwise2
from operator import itemgetter


def compress(all_a_words, all_a_ids, all_b_words, all_b_ids, window_size, recursive=True, verbose=False):
    print("Compressing, #words in A: "+str(len(all_a_words))+", #words in B: "+str(len(all_b_words)), file=sys.stderr)
    # Compress long trivial matches into single tokens prior to aligning
    del_in_a, del_in_b=set(),set()
    # Move window start over list of words in a
    for a_win_start in range(0, len(all_a_words)-(window_size-1)):
        # Skip as long as elem in window is marked as to be deleted already
        if a_win_start in del_in_a: continue
        # Extract words in window and create string.
        a_win_string=" ".join(all_a_words[a_win_start:a_win_start+window_size])
        # Move window over list of words in b, starting at the top
        for b_win_start in range(0, len(all_b_words)-(window_size-1)):
            # Skip as long as elem in window is marked as to be deleted already
            if b_win_start in del_in_b: continue
            b_win_string=" ".join(all_b_words[b_win_start:b_win_start+window_size])
            if a_win_string == b_win_string:
                # Write this to stderr even though verbose is set
                if verbose: print("Compressing '"+a_win_string+"'", file=sys.stderr)
                # Matching windows were found in both input lists
                # Replace string at window start with the matched string (this does the actual shirring)
                all_a_words[a_win_start] = a_win_string
                all_b_words[b_win_start] = b_win_string
                # Replace ID at window start with full id string (dito)
                all_a_ids[a_win_start] = "+".join(all_a_ids[a_win_start:a_win_start+window_size])
                all_b_ids[b_win_start] = "+".join(all_b_ids[b_win_start:b_win_start+window_size])

                # Mark last n-1 elements from n-element window for deletion
                for n in range(window_size-1,0,-1):
                    del_in_a.add(a_win_start+n)
                    del_in_b.add(b_win_start+n)
                # Stop after finding *the first match* of win_a in list b. 
                # This will only compress *the first* occurrence of each matching window in each list.
                break
    mod = False
    del_in_a=list(del_in_a)
    del_in_a.sort(reverse=True)
    for a in del_in_a:
        mod=True
        del all_a_words[a]
        del all_a_ids[a]

    del_in_b=list(del_in_b)
    del_in_b.sort(reverse=True)
    for b in del_in_b:
        mod=True
        del all_b_words[b]
        del all_b_ids[b]

    if mod and recursive:
        print("Recursing...", file=sys.stderr)
        return compress(all_a_words, all_a_ids, all_b_words, all_b_ids, window_size, recursive=recursive, verbose=verbose)

    return all_a_words, all_a_ids, all_b_words, all_b_ids


def conflate_hyphenated_ocr_splits(all_ocr_words, all_ocr_ids, all_pmc_words, all_pmc_ids, 
                                    fold=True, verbose=False):
    # conflated tokens receive +-separated ids
    # Go over list positions in ocr with a potential hyphen
    # ocr       pmc
    # X         X
    # ab        abcd
    # -         Y
    # cd
    # Y
    print("De-hyphenating...", file=sys.stderr)
    remove_idxs=[]
    for hyp_idx in [m for m in range(2,len(all_ocr_words)-2) if all_ocr_words[m] in ['-', '−', '–', '¬','-','-']]:
        # Reconstruct potential unhyphenated word
        rec_word=all_ocr_words[hyp_idx-1]+all_ocr_words[hyp_idx+1]
        # Go over list positions of all reconstructed words in pmc
        for pmc_idx in [p for p in range(1,len(all_pmc_words)-1) if (not fold and all_pmc_words[p]==rec_word) or (fold and all_pmc_words[p].lower() == rec_word.lower()) ]:
            # No case distinction required, just check context
            if  all_ocr_words[hyp_idx-2] and all_ocr_words[hyp_idx-2] == all_pmc_words[pmc_idx-1] \
            and all_ocr_words[hyp_idx+2] and all_ocr_words[hyp_idx+2] == all_pmc_words[pmc_idx+1]:
                if hyp_idx not in remove_idxs and hyp_idx+1 not in remove_idxs:
                    all_ocr_words[hyp_idx-1] = all_pmc_words[pmc_idx] # Overwrite hyphenated with unhyphenated word, using the latter's capitalization
                    all_ocr_ids[hyp_idx-1] = all_ocr_ids[hyp_idx-1]+"+"+all_ocr_ids[hyp_idx]+"+"+all_ocr_ids[hyp_idx+1]
                    if verbose: print("\t"+all_ocr_words[hyp_idx-1])
                    remove_idxs.append(hyp_idx)
                    remove_idxs.append(hyp_idx+1)

    # Remove backwards to be index-safe
    remove_idxs.sort(reverse=True)
    for a in remove_idxs:
        del all_ocr_words[a]
        del all_ocr_ids[a]
    return all_ocr_words, all_ocr_ids


def conflate_exact_ocr_splits(all_ocr_words, all_ocr_ids, all_pmc_words, all_pmc_ids, 
                                        recursive=True, verbose=False):
    #  Case:
    #  OCR           PMC
    #  X             X
    ## a             ab #
    #  b             Y
    #  Y             

    print("Conflating...", file=sys.stderr)
    remove_idxs=[]
    # Go over all list positions in ocr
    for ocr_idx in  [f for f in range(1,len(all_ocr_words)-2) if f not in remove_idxs]: # from -1 for lb, to -2 for max la 2
        # Create potential merged word from OCR, from ocr_idx + ocr_idx+1
        rec_word=all_ocr_words[ocr_idx] + all_ocr_words[ocr_idx+1]
        try:
            int(rec_word)
            continue                # Skip if rec_word is a number
        except ValueError:          pass
        # Go over list positions of all reconstructed word matches in pmc
        for pmc_idx in [p for p in range(1,len(all_pmc_words)-1) if all_pmc_words[p]==rec_word]: # from 1 for lb, to -1 for max la
            # No case distinction required, just check context
            if  all_ocr_words[ocr_idx-1] == all_pmc_words[pmc_idx-1] and all_ocr_words[ocr_idx+2] == all_pmc_words[pmc_idx+1]: 
                old_first_part=all_ocr_words[ocr_idx]
                old_second_part=all_ocr_words[ocr_idx+1]
                all_ocr_words[ocr_idx]  = rec_word    # Overwrite first splittee with merged word
                all_ocr_ids[ocr_idx]    = all_ocr_ids[ocr_idx] + "+" + all_ocr_ids[ocr_idx+1] # Merge two org ids as new id for merged token
                if ocr_idx+1 not in remove_idxs:
                    # Remove second splittee
                    remove_idxs.append(ocr_idx+1)
                    if verbose:     print("Conflated "+old_first_part+" + "+old_second_part+" ----> ",all_ocr_words[ocr_idx], all_ocr_ids[ocr_idx])

    # Remove backwards to be index-safe
    mod=False
    remove_idxs.sort(reverse=True)
    for a in remove_idxs:
        mod=True
        del all_ocr_words[a]
        del all_ocr_ids[a]

    if recursive and mod:
        print(str(len(remove_idxs))+" pre-conflations, recursing...", file=sys.stderr)
        return conflate_exact_ocr_splits(all_ocr_words, all_ocr_ids, all_pmc_words, all_pmc_ids, recursive=recursive, verbose=verbose)

    return all_ocr_words, all_ocr_ids


def split_exact_ocr_conflations(all_ocr_words, all_ocr_ids, all_pmc_words, all_pmc_ids, 
                                        recursive=True, verbose=False):
    # OK, PRE
    # Split wrongly merged ocr items
    # OCR           PMC
    # X             X
    # ab            a
    # Y             b
    #               Y
    print("Splitting...", file=sys.stderr)
    insert_idxs=[]
    # Go over all list positions in pmc
    for pmc_idx in range(len(all_pmc_words)-2):
        # Create potential merged word from pmc
        rec_word=all_pmc_words[pmc_idx]+all_pmc_words[pmc_idx+1]
        try:
            # Skip if rec_word is a number
            int(rec_word)
            continue
        except ValueError:  
            pass
        # Go over list positions of all reconstructed words matches in ocr
        for ocr_idx in [p for p in range(1,len(all_ocr_words)-1) if all_ocr_words[p]==rec_word]:
            # No case distinction required, just check context
            if all_pmc_words[pmc_idx-1] == all_ocr_words[ocr_idx-1] and all_pmc_words[pmc_idx+2] == all_ocr_words[ocr_idx+1]: 
                old_val=all_ocr_words[ocr_idx]
                all_ocr_words[ocr_idx]  = all_pmc_words[pmc_idx] # Overwrite with first part of correct word
                insert_idxs.append((ocr_idx+1,all_pmc_words[pmc_idx+1],all_ocr_ids[ocr_idx]))
                if verbose: print("Split "+old_val+" ----> " + all_pmc_words[pmc_idx]+" + "+all_pmc_words[pmc_idx+1], all_ocr_ids[ocr_idx])
    # Sort by insertion position
    mod=False
    insert_idxs.sort(key=itemgetter(0))
    for offset, (i,token,t_id) in enumerate(insert_idxs):
        mod=True
        all_ocr_words.insert(i+offset,token)
        all_ocr_ids.insert(i+offset,t_id)

    if recursive and mod:
        print(str(len(insert_idxs))+" pre-splits, recursing...", file=sys.stderr)
        return split_exact_ocr_conflations(all_ocr_words, all_ocr_ids, all_pmc_words, all_pmc_ids, recursive=recursive, verbose=verbose)

    return all_ocr_words, all_ocr_ids


def forcealign_tokens(ocr_words_aligned, ocr_ids_aligned, pmc_words_aligned, pmc_ids_aligned, 
                        alignments_performed, min_context_size=3, dynamic=True, recursive=True, gap_char="<<GAP>>", verbose=False):

    print("Force-aligning...", file=sys.stderr)
    # The forcealign to end all forcealigns. May the force(align) be with you!
    non_match_sequence, non_match_sequences, remove_idxs=[], [], []
    # This assumes alignment, so just one index required. Collect all *contiguous* non-aligned sequences 
    for idx in [a for a in range(len(ocr_words_aligned))]:
        if ocr_ids_aligned[idx] == "NONE" or pmc_ids_aligned[idx] == "NONE":    non_match_sequence.append(idx)
        else:
            if len(non_match_sequence)>0:   non_match_sequences.append(non_match_sequence)
            non_match_sequence=[]
    # Do not forget last one
    if len(non_match_sequence)>0:   non_match_sequences.append(non_match_sequence)

    last_nms_end_idx=0     # Store index of last nms end, for computing the size of the preceeding *matching* sequence (used as context)
    # Go over all mismatch sequences
    for nms_idx in range(len(non_match_sequences)):
        nms=non_match_sequences[nms_idx]
        # No. of elements in preceeding matching sequence,
        # (computed as diff. between the index of the first element of the current nms and the index of the last element of the preceeding one)
        left_match_size=nms[0]-last_nms_end_idx-1
        # Only if there is a right context
        if nms_idx<len(non_match_sequences)-1:  right_match_size=non_match_sequences[nms_idx+1][0]-nms[-1] # No. of elements in following matching sequence
        else:                                   right_match_size=min_context_size        

        # Try to identify four possible sub-sequences, splitting the lists in half
        top_ocr_words       =   [ocr_words_aligned[w] for w in nms[0               : int(len(nms)/2)]]
        top_pmc_words       =   [pmc_words_aligned[w] for w in nms[0               : int(len(nms)/2)]]
        bottom_ocr_words    =   [ocr_words_aligned[w] for w in nms[int(len(nms)/2) :                ]]
        bottom_pmc_words    =   [pmc_words_aligned[w] for w in nms[int(len(nms)/2) :                ]]

        # String rep of the current alignment, regardless of whether it will be done or not
        alignment_key = ("".join(top_ocr_words)+" <-> "+("".join(bottom_pmc_words)))
        # Context size must be sufficient, **unless** dynamic=True and the particular alignment has been done before (in sufficient context)
        if (left_match_size < min_context_size or right_match_size < min_context_size): continue # and not (dynamic and alignment_key in alignments_performed) :   continue
        # Check if top half of PMC is gap and bottom half of OCR is gap (the other constellation does not seem to occur)
        if len(nms) % 2 == 0 and  top_pmc_words == [gap_char]*int(len(nms)/2) and bottom_ocr_words == [gap_char]*int(len(nms)/2):
            if verbose: print("Symmetric gaps: left context, right context", left_match_size, right_match_size, file=sys.stderr)

            # Output the left and right CONTEXT also 
            
            # Todo: Make this more elegant, with *one* algo for arbitrary len(nms)
            # Symmetrical gap pattern
            if len(nms)==2:
                if verbose: print("\tForcing " + str(top_ocr_words) + " --1--> " + str(bottom_pmc_words))
                pmc_words_aligned[nms[0]] = pmc_words_aligned[nms[1]]
                pmc_ids_aligned[nms[0]]   = pmc_ids_aligned[nms[1]]
                remove_idxs.append(nms[1])
                alignments_performed[0].update({alignment_key})
            elif len(nms)==4:
                if verbose: print("\tForcing " + str(top_ocr_words) + " --2--> " + str(bottom_pmc_words))
                pmc_words_aligned[nms[0]] = pmc_words_aligned[nms[2]]
                pmc_ids_aligned[nms[0]]   = pmc_ids_aligned[nms[2]]
                pmc_words_aligned[nms[1]] = pmc_words_aligned[nms[3]]
                pmc_ids_aligned[nms[1]]   = pmc_ids_aligned[nms[3]]

                remove_idxs.extend([nms[2],nms[3]])
                alignments_performed[0].update({alignment_key})
                #previous_valid_alignments.add(alignment_key)
            elif len(nms)==6:
                if verbose: print("\tForcing " + str(top_ocr_words) + " --3--> " + str(bottom_pmc_words))
                pmc_words_aligned[nms[0]] = pmc_words_aligned[nms[3]]
                pmc_ids_aligned[nms[0]]   = pmc_ids_aligned[nms[3]]
                pmc_words_aligned[nms[1]] = pmc_words_aligned[nms[4]]
                pmc_ids_aligned[nms[1]]   = pmc_ids_aligned[nms[4]]
                pmc_words_aligned[nms[2]] = pmc_words_aligned[nms[5]]
                pmc_ids_aligned[nms[2]]   = pmc_ids_aligned[nms[5]]

                remove_idxs.extend([nms[3],nms[4],nms[5]])
                alignments_performed[0].update({alignment_key})
                #previous_valid_alignments.add(alignment_key)
            elif len(nms)==8:
                if verbose: print("\tForcing " + str(top_ocr_words) + " --4--> " + str(bottom_pmc_words))
                pmc_words_aligned[nms[0]] = pmc_words_aligned[nms[4]]
                pmc_ids_aligned[nms[0]]   = pmc_ids_aligned[nms[4]]
                pmc_words_aligned[nms[1]] = pmc_words_aligned[nms[5]]
                pmc_ids_aligned[nms[1]]   = pmc_ids_aligned[nms[5]]
                pmc_words_aligned[nms[2]] = pmc_words_aligned[nms[6]]
                pmc_ids_aligned[nms[2]]   = pmc_ids_aligned[nms[6]]
                pmc_words_aligned[nms[3]] = pmc_words_aligned[nms[7]]
                pmc_ids_aligned[nms[3]]   = pmc_ids_aligned[nms[7]]

                remove_idxs.extend([nms[4],nms[5],nms[6],nms[7]])
                alignments_performed[0].update({alignment_key})

        last_nms_end_idx=nms[-1]

    mod=False
    remove_idxs.sort(reverse=True)
    for i in remove_idxs:
        mod=True
        del ocr_words_aligned[i]
        del ocr_ids_aligned[i]
        del pmc_words_aligned[i]
        del pmc_ids_aligned[i]
    
    if recursive and mod:
        print(str(len(remove_idxs))+" forced alignments, recursing...", file=sys.stderr)
        return forcealign_tokens(ocr_words_aligned, ocr_ids_aligned, pmc_words_aligned, pmc_ids_aligned, 
                                    alignments_performed, min_context_size=min_context_size, gap_char=gap_char, dynamic=dynamic, recursive=recursive, verbose=verbose)

    # alignments_performed will be returned implicitly
    return ocr_words_aligned, ocr_ids_aligned, pmc_words_aligned, pmc_ids_aligned


def check_alignment(ocr_words_aligned, pmc_words_aligned, ocr_ids_aligned, pmc_ids_aligned):
    try:    
        assert len(ocr_words_aligned) == len(pmc_words_aligned) == len(ocr_ids_aligned) == len(pmc_ids_aligned)
    except AssertionError:
        print("ocr_words", len(ocr_words_aligned))
        print("pmc_words", len(pmc_words_aligned))
        print("ocr_ids", len(ocr_ids_aligned))
        print("pmc_ids", len(pmc_ids_aligned))
        raise

def align_tokens(ocr_words, ocr_ids, pmc_words, pmc_ids, method="global", filler="NONE", gap_char="<<GAP>>", verbose=False):
    if verbose: print("Aligning "+str(len(ocr_words)+len(pmc_words)) +" tokens...", file=sys.stderr)
    # Create approximate alignment of ocr tokens and pmc tokens
    if method=="local":
        alignments = pairwise2.align.localxx(ocr_words, pmc_words, gap_char=[gap_char], one_alignment_only=True)
    elif method=="global":
        alignments = pairwise2.align.globalxx(ocr_words, pmc_words, gap_char=[gap_char], one_alignment_only=True)
    else:
        print("No such alignment method:"+method)
        return [],[],[],[]
    alignment  = None if len(alignments) == 0 else alignments[0]
    if alignment:
        assert len(alignment.seqA) == len(alignment.seqB)
        # Add spacers to id lists for current sublist to keep them aligned with their corresponding word lists
        for a in range(len(alignment.seqA)):
            if alignment.seqA[a] == gap_char:  ocr_ids.insert(a,filler) # Add spacer
            if alignment.seqB[a] == gap_char:  pmc_ids.insert(a,filler) # Add spacer

    if verbose: print(str(len(ocr_ids))+" partially aligned pairs", file=sys.stderr)
    return alignment.seqA, ocr_ids, alignment.seqB, pmc_ids

def jaccard_similarity_set(string1, string2):
    set1=set([c for c in string1])
    set2=set([c for c in string2])

    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    return intersection / union


def interpolate_span(span, max_gap=1):
    new_span=[]
    for i in range(int(span[0].split("_")[1]), int(span[-1].split("_")[1])+1):
        new_span.append("word_"+str(i))
    return new_span

def create_id_to_id_mapping(ocr_words_aligned, pmc_words_aligned, ocr_ids_aligned, pmc_ids_aligned):
    # Create ID to ID mapping from OCR (key) to PMC (value)
    # In the result, OCR ids (as keys) will always be single IDs, but PMC ids (as values) can be lists (Case 2)

    # Case 1: Conflation (works the same in pre- and post-processing)
    # OCR:              PMC:
    # c     word_2      GAP     NONE
    # m     word_3      GAP     NONE
    # GAP   NONE        cm      word_45
    # --> 
    # cm    word_2+word_3   cm  word_45
    # in dict: word_2 -> word_45, word_3 -> word_45

    # Case 2: Splitting (dito)
    # 99x   word_4      GAP     NONE
    # GAP   NONE        99      word_67
    # GAP   NONE        x       word_68
    # -->
    # 99    word_4      99      word_67
    # x     word_4      x       word_68
    # in dict: word_4 -> word_67+word_68

    # Case 3: Compression

    # Go over all ocr words. Each one has an id, which is either 
    # - NONE (if the word is a GAP char inserted during alignment),
    # - a single MMAX2 basedata id of the form word_XXX, or 
    # - a +-separated sequence of the above, if they were conflated during pre- or post-processing, or compressed afterwards

    ocr2pmc={}
    for i in range(len(ocr_words_aligned)):
        if ocr_ids_aligned[i] != "NONE" and pmc_ids_aligned[i] != "NONE":
            # Both IDs id might be complex (PMC only as a result of compression)
            ocr_id_list     = ocr_ids_aligned[i].split("+")
            pmc_id_list     = pmc_ids_aligned[i].split("+")
            if len(ocr_id_list)==1 and len(pmc_id_list)==1:
                # There is a one-to-one mapping from OCR id to PMC id
                # However, the OCR might have a PMC id mapped to it already (Case 2 above)
                # Nothing yet, just add new ocr-pmc mapping
                if ocr_id_list[0] not in ocr2pmc:   ocr2pmc[ocr_id_list[0]] = pmc_id_list[0]
                # Mapping exists already for ocr_id, so add pmc_id to existing key   
                else:                               ocr2pmc[ocr_id_list[0]] = ocr2pmc[ocr_id_list[0]] + "+" + pmc_id_list[0]

            elif len(ocr_id_list)==1 and len(pmc_id_list)>1:
                # pmc_id_list can only be >1 if pmc words were compressed earlier.
                if ocr_id_list[0] not in ocr2pmc:   ocr2pmc[ocr_id_list[0]] = "+".join(pmc_id_list)
                else:
                    tmp="+".join(pmc_id_list)
                    ocr2pmc[ocr_id_list[0]] = ocr2pmc[ocr_id_list[0]]+ "+" + tmp
            elif len(ocr_id_list)>1 and len(pmc_id_list)==1:
                # More than one ocr_id is mapped to precisely one pmc_id
                for ocr_id in ocr_id_list:
                    if ocr_id not in ocr2pmc:       ocr2pmc[ocr_id] = pmc_id_list[0]
                    else:                           ocr2pmc[ocr_id] = ocr2pmc[ocr_id]+ "+" + pmc_id_list[0]
            else:                
                # Several OCR ids map to several PMC ids
                if len(ocr_id_list)==len(pmc_id_list):
                    # Just do a one-to-one mapping
                    for ocr_id,pmc_id in zip(ocr_id_list,pmc_id_list):                    
                        if ocr_id not in ocr2pmc:   ocr2pmc[ocr_id] = pmc_id
                        else:                       ocr2pmc[ocr_id] = ocr2pmc[ocr_id] + "+" + pmc_id
                else:
                    # n to m mapping
                    tmp="+".join(pmc_id_list)
                    for ocr_id in ocr_id_list:
                        if ocr_id not in ocr2pmc:   ocr2pmc[ocr_id] = tmp
                        else:                       ocr2pmc[ocr_id] = ocr2pmc[ocr_id]+ "+" + tmp
    return ocr2pmc
