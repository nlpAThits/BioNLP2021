# BioNLP2021

This is the code repository for the paper [Word-Level Alignment of Paper Documents with their Electronic Full-Text Counterparts](https://www.aclweb.org/anthology/2021.bionlp-1.19.pdf)


For questions, you can contact [Mark-Christoph Müller](mailto:mark-christoph.mueller@h-its.org?subject=bionlp2021)

*Setup*

The alignment code uses the MMAX2 data format internally, so installing pyMMAX2 is **required**. 
Installing the Java-based MMAX2 annotation tool is required for viewing the aligned data, and is therefore recommended.

```console
conda create -n bionlp2021 python=3.7
source activate bionlp2021
git clone https://github.com/nlpAThits/BioNLP2021
cd BioNLP2021
pip install -r requirements.txt
git clone https://github.com/nlpAThits/pyMMAX2
pip install pyMMAX2/.
git clone https://github.com/nlpAThits/MMAX2
```

*Convert sample PMC-NXML to MMAX2 Format*
```console
(bionlp2021) foo@bar:~$  python ./code/pmc2mmax.py --pmc_path ./data/nxml/PMC3958920.nxml --mmax2_base_path ./data/MMAX2/from_nxml/
```
```console
Level file name set to PMC3958920_structure_markables.xml
Markables at ./data/MMAX2/from_nxml/./Markables/PMC3958920_structure_markables.xml not found, skipping!
Level file name set to PMC3958920_alignments_markables.xml
Markables at ./data/MMAX2/from_nxml/./Markables/PMC3958920_alignments_markables.xml not found, skipping!

MMAX2 Project Info:
-------------------
.mmax file        : ./data/MMAX2/from_nxml/PMC3958920.mmax
Basedata elements : 8532
Markable levels   :
 structure        :   506 markables [DEFAULT: none defined]
 alignments       :     0 markables [DEFAULT: none defined]
```

*Open file in MMAX2 annotation tool*

(This is optional.)
```console
(bionlp2021) foo@bar:~$ cd MMAX2
(bionlp2021) foo@bar:~$ ./mmax2_flex.sh ../data/MMAX2/from_nxml/PMC3958920.mmax
```
<img src="./docs/images/mmax2_shot1.png" alt="drawing" width="50%"/>

*Convert sample PDF to MMAX2 Format (via PNG)*

The following command expects the non-standard tessdata model at the provided path.
```console
(bionlp2021) foo@bar:~$ python ./code/pdf2mmax.py --pdf_path ./data/pdf/real-pdf/PMC3958920.pdf  --mmax2_base_path ./data/MMAX2/from_png/converted/ --force_new_mmax2 --png_base_path ./data/temp_png/ --force_new_png --dpi 300 --tessdata_dir /usr/share/tesseract-ocr/4.00/tessdata_best
```
```console
Level file name set to PMC3958920_ocr_words_level.xml
Markables at ./data/MMAX2/from_png/converted/Markables/PMC3958920_ocr_words_level.xml not found, skipping!
Level file name set to PMC3958920_ocr_lines_level.xml
Markables at ./data/MMAX2/from_png/converted/Markables/PMC3958920_ocr_lines_level.xml not found, skipping!
Level file name set to PMC3958920_alignments_markables.xml
Markables at ./data/MMAX2/from_png/converted/Markables/PMC3958920_alignments_markables.xml not found, skipping!
	Converting ./data/pdf/real-pdf/PMC3958920.pdf to 300 dpi PNG file ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-01.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-02.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-03.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-04.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-05.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-06.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-07.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-08.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-09.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-10.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
	File ./data/temp_png//PMC3958920.pdf@300DPI-page-11.png
		OCR ...
		BS4 ...
		hOCR2MMAX2 ...
```

*Open file in MMAX2 annotation tool*
```console
(bionlp2021) foo@bar:~$ cd ../MMAX2/
(bionlp2021) foo@bar:~$ ./mmax2_flex.sh ../BioNLP2021/data/MMAX2/from_png/converted/PMC3958920.mmax
```
<img src="./docs/images/mmax2_shot2.png" alt="drawing" width="50%"/>

*Create a word-level alignment of the two documents*
```console
(bionlp2021) foo@bar:~$ python 
```
