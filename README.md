# ngsderive

[![CI status](https://github.com/claymcleod/ngsderive/workflows/CI/badge.svg)](https://github.com/claymcleod/ngsderive/actions)

`ngsderive` is a set of utilities developed to backwards compute various attributes from
next-generation sequencing data. This command line utility only implements
commands which were not available at the time of writing in common NGS utilities
(e.g., [Picard](https://broadinstitute.github.io/picard/)). All utilities are
provided as-is with no warranties: many tools just provide suggestions, and
though we've done the best we can + this toolkit evolves as we learn more, we 
don't claim 100% accuracy for all utilities provided.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Installing

To get started with `ngsderive`, you can install it using pip:

```bash
pip install git+https://github.com/claymcleod/ngsderive.git
```

Currently, the following commands are supported:

```bash
> ngsderive                                                                                                                                                      ✔  6699  12:12:51
Usage:
  ngsderive readlen <ngsfiles>... [--outfile=<outfile>]
  ngsderive machine <ngsfiles>... [--outfile=<outfile>]
  ngsderive (-h | --help)
  ngsderive --version
```

## Usage

### Illumina machine type

The `ngsderive instrument` subcommand will attempt to backward compute the
machine that generated a NGS file using (1) the instrument id(s) and (2) the
flowcell id(s). Note that this command may not comprehensively detect the
correct machines as there is no published catalog of Illumina serial numbers.
As we encounter more serial numbers in practice, we update this code.

### Read length calculation

Using the `ngsderive readlen` subcommand, one can backward compute the
readlength used during sequencing. Currently, the algorithm used is roughly:

1. Compute distribution of read lengths for the first `n` reads in a file
   (default: 10000).
2. If the maximum read length makes up `p`% of the reads, the read length is
   equal to that number (e.g., if 85% percent of the reads are 100bp, then the
   read length is considered 100bp.)
3. If #2 does not hold true, the read length cannot be computed confidently.

### Strandedness inference

Strandedness can estimated by observing the following characteristics of a particular read:

* Whether the read is read 1 or read 2 ("read ordinal").
* Whether the read was aligned to the + or - strand ("read strand")
* Given a gene model, whether a feature of interest (usually a gene) falls on the + or - strand.

A shorthand notation for the state of a read can be achieved by simply concatenating the three
characteristics above (e.g., `1+-` means that a read 1 was aligned to the positive strand and a gene
was observed at the same location on the negative strand).

Given the notation above, the following lookup table can be used to see whether a read is evidence for
forward-strandedness or reverse-strandedness:

| Patterns                   | Evidence for strandedness type |
| -------------------------- | ------------------------------ |
| `1++`, `1--`, `2+-`, `2-+` | Forward                        |
| `2++`, `2--`, `1+-`, `1-+` | Reverse                        |

By default, the strandedness check is designed to work with the [GENCODE][gencode-website] geneset. Either a GTF or GFF file can be used as the gene model — you can use the following one liners to prepare the latest geneset at the time of writing for hg19 and hg38 respectively.

```bash
# hg19
curl ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_32/GRCh37_mapping/gencode.v32lift37.annotation.gtf.gz | gunzip -c | sort -k1,1 -k4,4n -k5,5n | bgzip > gencode.v32lift37.annotation.gtf.gz
tabix -p gff gencode.v32lift37.annotation.gtf.gz

# hg38
curl ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_32/gencode.v32.annotation.gff3.gz | gunzip -c | sort -k1,1 -k4,4n -k5,5n | bgzip > gencode.v32.annotation.gff3.gz
tabix -p gff gencode.v32.annotation.gff3.gz
```

At the time of writing, the algorithm works roughly like this:

1. The gene model is read in and only `gene` features are retained.
2. For `--n-genes` times, a randomly sampled gene is selected from the gene model. The gene must pass a quality check. Of particular interest,
   1. The gene must not be an overlapping feature on the opposite strand which would present ambiguous results.
   2. *Optionally*, the gene must be a protein coding gene.
   3. *Optionally*, the gene must have at least `--minimum-reads-per-gene` minimum reads per gene.
3. All of the reads from that region of the genome are extracted and put through several quality filters including but not limited to:
   1. The read must not be marked as QC-failed.
   2. The read must not be marked as a duplicate.
   3. The read must not be marked as secondary.
   4. The read must not be unmapped.
   5. *Optionally*, the read have a minimum MAPQ score.
4. For all reads that pass the above filters, compute the evidence and tally results.

The most popular strandedness inference tool that the author is aware of is RSeQC's [infer_experiment.py](http://rseqc.sourceforge.net/#infer-experiment-py). The main difference is that RSeQC starts at the beginning of the BAM file and takes the first `n` reads that match its criteria. If the BAM is coordinate sorted, this would mean its not uncommon to have all of the evidence at the beginning of `chr1`. Anecdotally, this method differs in that it is slightly slower than `infer_experiment.py` but is expected to be more robust to biases caused by which reads are sampled.

### Limitations

* Does not yet work with single-end data (simply because the author doesn't have any on hand). The tool will throw an error if any unpaired reads are discovered (let us know in the issues if you need this supported).
* Though hundreds of Unstranded and Stranded-Reverse data has been tested and verified, Stranded-Forward data has not been tested to work with this tool (simply because the author doesn't have on hand). We do not anticipate any issues since Stranded-Reverse is working well.

## Running the tests

```bash
> py.test
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed as follows:
* All code related to the `instrument` subcommand is licensed under the [AGPL
  v2.0][agpl-v2]. This is not due any strict requirement, but out of deference
  to some [code][10x-inspiration] I drew inspiration from (and copied patterns
  from), the decision was made to license this code consistently.
* The rest of the project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

[10x-inspiration]: https://github.com/10XGenomics/supernova/blob/master/tenkit/lib/python/tenkit/illumina_instrument.py
[agpl-v2]: http://www.affero.org/agpl2.html
[gencode-website]: https://www.gencodegenes.org/
