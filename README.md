# Vaccine Ontology Quality Assurance using Lexical Characteristics
Lexical Based semi-automated Quality Assurance for Vaccine Ontology

## About
Lexical based approach for the identification of potential missing is-a relations within the [Vaccine Ontology](https://www.violinet.org/vaccineontology/)

## Requirements
* [Owlready2](https://owlready2.readthedocs.io/en/latest/index.html)
* [pandas](https://pandas.pydata.org/)

## Inputs
This script requires two inputs:
1. Ontology File: An .owl file containing the ontology
2. Root IRI: The identifier for the root for which unlinked concepts will be exhaustively searched for (The IRI of a concept can be retrieved through an Ontology viewer such as [Protege](https://protege.stanford.edu/). Right click on the concept and select copy IRI)

## Usage
~python OntoReader.oy <Ontology .owl file> <Root IRI for unlinked pairs>