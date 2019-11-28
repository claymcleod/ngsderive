import csv
import itertools
import logging
import pysam
import sys

from collections import defaultdict

logger = logging.getLogger('readlen')

def main(ngsfiles,
         outfile=sys.stdout,
         delimiter="\t",
         n_samples=100000,
         majority_vote_cutoff=0.7):

    writer = csv.DictWriter(
        outfile,
        fieldnames=["File", "Evidence", "MajorityPctDetected", "Consensusread length"],
        delimiter=delimiter)
    writer.writeheader()

    for ngsfile in ngsfiles:
        read_lengths = defaultdict(int)
        samfile = pysam.AlignmentFile(ngsfile, "rb")

        # accumulate read lengths
        total_reads_sampled = 0
        for read in itertools.islice(samfile, n_samples):
            total_reads_sampled += 1
            read_lengths[len(read.query)] += 1

        read_length_keys_sorted = sorted([int(k) for k in read_lengths.keys()], reverse=True)
        putative_max_readlen = read_length_keys_sorted[0]

        # note that simply picking the read length with the highest amount of evidence
        # doesn't make sense — things like adapter trimming might shorten the read length,
        # but the read length should never grow past the maximum value.

        # if not, cannot determine, return -1
        pct = read_lengths[putative_max_readlen] / total_reads_sampled 
        logger.info("Max read length percentage: {}".format(pct))
        majority_readlen = putative_max_readlen if pct > majority_vote_cutoff else -1

        result = {
            "File":
            ngsfile,
            "Evidence":
            ";".join([
                "{}={}".format(k, read_lengths[k])
                for k in read_length_keys_sorted
            ]),
            "MajorityPctDetected": round(pct, 4),
            "ConsensusReadLength":
            majority_readlen
        }

        writer.writerow(result)
