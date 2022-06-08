# Vaccine Ontology Quality Assurance using Lexical Characteristics

## About
Lexical based approach for the identification of potential missing is-a relations within the [Vaccine Ontology](https://www.violinet.org/vaccineontology/)

## Requirements
* [Owlready2](https://owlready2.readthedocs.io/en/latest/index.html)
* [pandas](https://pandas.pydata.org/)

## Inputs
This script requires two inputs:
1. Ontology File: An .owl file containing the ontology
2. Root IRI: The identifier for the root for which unlinked concepts will be exhaustively searched for (The IRI of a concept can be retrieved through an Ontology viewer such as [Protege](https://protege.stanford.edu/). Right click on the concept and select copy IRI)

## Outputs
Two output files will be generated
1. `<ontology>_expanded_output_<date>.csv` : All detected inconsistencies
    * Word Difference : The word difference between the two concepts (C1-C2),(C2-C1)
	* C1 (Linked) : Linked Child Concept ID
	* Label1 : Linked Child Concept Label
	* C2 (Linked) : Linked Parent Concept ID
	* Label2 : Linked Parent Concept Label
	* C1 (Unlinked) : Unlinked Child Concept ID
	* Label3 : Unlinked Child Concept Label
	* C2 (Unlinked) : Unlinked Parent Concept ID
	* Label4 : Unlinked Parent Concept Label
    
1. `<ontology>_is_a_inconsistencies_<date>.csv` : The potential missing *is-a* relationships with the following columns
	* Word Difference : The word difference between the two concepts (C1-C2),(C2-C1)
	* Unlinked Pair : Unlinked Concept Pair generating the word difference
	* Linked Pairs : Consolidated list of Linked Concept Pairs generating the word difference mentioned above

## Usage
`python OntoReader.py <Ontology .owl file> <Root IRI for unlinked pairs>`\
**ex:** \
`python OntoReader.py VO.owl http://purl.obolibrary.org/obo/BFO_0000040`