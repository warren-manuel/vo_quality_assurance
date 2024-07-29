from itertools import count
from datetime import date
import pandas as pd
from owlready2 import get_ontology, IRIS


class OntoReader:
    def __init__(self, file):
        self.labeldict = {}
        self.anclist = {}
        self.linked_con_pairs = set()
        self.unlinked_con_pairs = set()
        self.atp_dict_linked = {}
        self.atp_dict_unlinked = {}
        self.inverted_index_linked = {}
        self.inverted_index_unlinked = {}

        self.onto = get_ontology(file).load()
        special_chars = {"'", "(", ")", ","}

        for concept in self.onto.classes():
            name = str(concept)
            text = str(concept.label)
            for char in special_chars:
                text = text.replace(char, " ")
            text = text.strip("[]").lower()
            labellist = set(text.split())
            anc = {str(ancestor) for ancestor in concept.ancestors(include_self=False)}
            anc.discard('owl.Thing')

            self.labeldict[name] = {'name': name, 'label': concept.label, 'list': labellist, 'ancestors': anc}
            self.anclist[name] = anc

        print("OntoReader object created successfully")

    def linked_methods(self):
        print("Detecting linked pairs")
        for c1, ancestors in self.anclist.items():
            for c2 in ancestors:
                self.linked_con_pairs.add((c1, c2))

        for c1, c2 in self.linked_con_pairs:
            c1set = self.labeldict[c1]['list']
            c2set = self.labeldict[c2]['list']
            if c1set != c2set and c1set & c2set:
                atp = (frozenset(c1set - c2set), frozenset(c2set - c1set))
                self.atp_dict_linked[(c1, c2)] = atp

        for con_pair, atp in self.atp_dict_linked.items():
            self.inverted_index_linked.setdefault(atp, []).append(con_pair)

    def unlinked_methods(self, root_node):
        print("Detecting unlinked pairs")
        root = IRIS[root_node]

        for cls in self.onto.get_children_of(root):
            text = str(cls.label).replace("(", " ").replace(")", " ").replace("'", " ").replace(",", " ").strip("[]").lower()
            label = set(text.split())

            if "obsolete" not in label:
                desc = {str(de) for de in cls.descendants()}
                for d1 in desc:
                    for d2 in desc:
                        if d1 != d2 and d2 not in self.anclist[d1] and d1 not in self.anclist[d2] and \
                                self.labeldict[d1]['name'][:6] == self.labeldict[d2]['name'][:6]:
                            self.unlinked_con_pairs.add((d1, d2))

        for c1, c2 in self.unlinked_con_pairs:
            c1set = self.labeldict[c1]['list']
            c2set = self.labeldict[c2]['list']
            if c1set & c2set:
                atp = (frozenset(c1set - c2set), frozenset(c2set - c1set))
                self.atp_dict_unlinked[(c1, c2)] = atp

        for con_pair, atp in self.atp_dict_unlinked.items():
            self.inverted_index_unlinked.setdefault(atp, []).append(con_pair)

    def detect_inconsistencies(self):
        print("Detecting inconsistencies")
        today = date.today()
        mismatch = {}
        expanded_out = {}

        for atp, unlinked_pairs in self.inverted_index_unlinked.items():
            if atp in self.inverted_index_linked:
                set1, set2 = atp
                mismatch[tuple(set1), tuple(set2)] = {
                    'linked': self.inverted_index_linked[atp],
                    'unlinked': unlinked_pairs
                }

        for atp, pairs in mismatch.items():
            linked_pairs = pairs['linked']
            unlinked_pairs = pairs['unlinked']

            for i, linked_pair in enumerate(linked_pairs):
                for j, unlinked_pair in enumerate(unlinked_pairs):
                    expanded_out[(i, j, atp)] = {
                        'Word Difference': atp,
                        'C1 (Linked)': linked_pair[0],
                        'Label1': self.labeldict[linked_pair[0]]['label'],
                        'C2 (Linked)': linked_pair[1],
                        'Label2': self.labeldict[linked_pair[1]]['label'],
                        'C1 (Unlinked)': unlinked_pair[0],
                        'Label3': self.labeldict[unlinked_pair[0]]['label'],
                        'C2 (Unlinked)': unlinked_pair[1],
                        'Label4': self.labeldict[unlinked_pair[1]]['label']
                    }

        df = pd.DataFrame(expanded_out.values())
        df.to_csv(f"{file}_expanded_output_{today}.csv")

        is_a_inference = {}
        for atp, pairs in mismatch.items():
            for unlinked_pair in pairs['unlinked']:
                is_a_inference[(atp, unlinked_pair)] = {
                    'Word Difference': atp,
                    'Unlinked Pair': unlinked_pair,
                    'U_Label1': self.labeldict[unlinked_pair[0]]['label'],
                    'U_Label2': self.labeldict[unlinked_pair[1]]['label'],
                    'L_Label1': self.labeldict[pairs['linked'][0][0]]['label'],
                    'L_Label2': self.labeldict[pairs['linked'][0][1]]['label'],
                    'Linked Pairs': pairs['linked']
                }

        df1 = pd.DataFrame(is_a_inference.values())
        df1.to_csv(f"{file}_is_a_inconsistencies_{today}.csv")


def main(file, root):
    ont_obj = OntoReader(file)
    ont_obj.linked_methods()
    ont_obj.unlinked_methods(root)
    ont_obj.detect_inconsistencies()

if __name__ == '__main__':
    main()
