import csv
import itertools
import pysam
import sys

import logging
from collections import defaultdict

from ..utils import NGSFile, NGSFileType

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SANGER_SET = set([i for i in range(33, 127)])
ILLUMINA_1_0_SET = set([i for i in range(59, 127)])
ILLUMINA_1_3_SET = set([i for i in range(64, 127)])

def main(ngsfiles,
         outfile=sys.stdout,
         delimiter="\t",
         n_samples=1000000):
    
    writer = csv.DictWriter(outfile,
                            fieldnames=[
                                "File", "Evidence", "ProbableEncoding"
                            ],
                            delimiter=delimiter)
    writer.writeheader()
    outfile.flush()

    if n_samples < 1:
      n_samples = None

    for ngsfilepath in ngsfiles:
        read_lengths = defaultdict(int)
        try:
            ngsfile = NGSFile(ngsfilepath, store_qualities=True)
        except FileNotFoundError:
            result = {
                "File": ngsfilepath,
                "Evidence": "File not found.",
                "ProbableEncoding": "N/A"
            }
            writer.writerow(result)
            outfile.flush()
            continue

        if ngsfile.filetype != NGSFileType.FASTQ:
            raise RuntimeError(
                "Invalid file: {}. `encoding` currently only supports FASTQ files!"
                .format(ngsfilepath))

        score_set = set()
        for read in itertools.islice(ngsfile, n_samples):
            for char in read['quality']:
                score_set.add(ord(char))
        
        max_phred_score = chr(max(score_set))
        min_phred_score = chr(min(score_set))
        if score_set <= ILLUMINA_1_3_SET:
            result = {
                "File": ngsfilepath,
                "Evidence": "Phred range: {}-{}".format(min_phred_score, max_phred_score),
                "ProbableEncoding": "Illumina 1.3"
            }
        elif score_set <= ILLUMINA_1_0_SET:
            result = {
                "File": ngsfilepath,
                "Evidence": "Phred range: {}-{}".format(min_phred_score, max_phred_score),
                "ProbableEncoding": "Solexa/Illumina 1.0"
            }
        elif score_set <= SANGER_SET:
            result = {
                "File": ngsfilepath,
                "Evidence": "Phred range: {}-{}".format(min_phred_score, max_phred_score),
                "ProbableEncoding": "Sanger/Illumina 1.8"
            }
        else:
            result = {
                "File": ngsfilepath,
                "Evidence": "Phred values outside known encoding ranges: {}-{}".format(min_phred_score, max_phred_score),
                "ProbableEncoding": "Unknown"
            }
        
        writer.writerow(result)
        outfile.flush()
