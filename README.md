# BioNLP2021

This is the code repository for the paper 

Word-Level Alignment of Paper Documents with their Electronic Full-Text Counterparts

The code will be made available for the workshop.

For questions, you can contact [Mark-Christoph Müller](mailto:mark-christoph.mueller@h-its.org?subject=bionlp2021)

*Setup*

```console
conda create -n bionlp2021 python=3.7
source activate bionlp2021
git clone https://github.com/nlpAThits/MMAX2
git clone https://github.com/nlpAThits/BioNLP2021
cd BioNLP2021
pip install -r requirements.txt
git clone https://github.com/nlpAThits/pyMMAX2
pip install pyMMAX2/.
```

*Convert sample PMC-NXML to MMAX2 Format*
```console
(bionlp2021) ~/BioNLP2021$ python ./code/pmc2mmax.py --pmc_path ./data/nxml/PMC3958920.nxml --mmax2_base_path ./data/MMAX2/from_nxml/
```
