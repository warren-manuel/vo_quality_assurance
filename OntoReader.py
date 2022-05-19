from itertools import count
import time
from datetime import date
import csv
import re
import pandas as pd
from urllib.request import AbstractDigestAuthHandler
from owlready2 import *


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
        for concept in self.onto.classes():
            name = str(concept)
            text = str(concept.label)
            # print(text)
            specialChars = {"'", "(", ")", ","}
            for specialChar in specialChars:
                text = text.replace(specialChar, " ")
            text = str(text)[2:-2]
            labellist = set(text.lower().split())
            anc = set()
            for ancestor in concept.ancestors(include_self=False):
                anc.add(str(ancestor))
            self.labeldict[name] = {'name': name, 'label': concept.label, 'list': labellist, 'ancestors': anc}
            self.anclist[name] = anc

    def linked_methods(self):
        for c1 in self.anclist:
            for c2 in self.anclist[c1]:
                self.linked_con_pairs.add((c1, c2))
        for c1, c2 in self.linked_con_pairs:
            c1set = set(self.labeldict[str(c1)]['list'])
            c2set = set(self.labeldict[str(c2)]['list'])
            if len(c2set.intersection(c1set)) != 0 and c1set != c2set:
                d1 = c1set.difference(c2set)
                d2 = c2set.difference(c1set)
                fsd1 = frozenset(d1)
                fsd2 = frozenset(d2)
                atp = fsd1, fsd2
                self.atp_dict_linked[str(c1), str(c2)] = atp
        for con_pair in self.atp_dict_linked.keys():
            con_pairs_list = []
            atp = self.atp_dict_linked[con_pair]
            if atp in self.inverted_index_linked.keys():
                for y in self.inverted_index_linked[atp]:
                    con_pairs_list.append(y)
                con_pairs_list.append(con_pair)
                self.inverted_index_linked[atp] = con_pairs_list
            else:
                con_pairs_list.insert(0, con_pair)
                self.inverted_index_linked[atp] = con_pairs_list

    def unlinked_methods(self, root_node):
        root = IRIS[root_node]
        for cls in self.onto.get_children_of(root):
            text = str(cls.label)
            specialChars = {"'", "(", ")", ","}
            for specialChar in specialChars:
                text = text.replace(specialChar, " ")
            text = str(text)[2:-2]
            label = set(text.lower().split())
            if "obsolete" not in label:  # ignoring obsolete classes
                print(cls.label)
                desc = []
                for de in cls.descendants():
                    desc.append(str(de))
                for d1 in desc:
                    for d2 in desc:
                        if d1 == d2 or d2 in self.anclist[d1] or d1 in self.anclist[d2] or self.labeldict[d1]['name'][
                                                                                           0:6] != \
                                self.labeldict[d2]['name'][0:6]:
                            continue
                        else:
                            self.unlinked_con_pairs.add((d1, d2))
            else:
                continue
        for c1, c2 in self.unlinked_con_pairs:
            c1set = set(self.labeldict[str(c1)]['list'])
            c2set = set(self.labeldict[str(c2)]['list'])
            if len(c2set.intersection(c1set)) != 0:
                d1 = c1set.difference(c2set)
                d2 = c2set.difference(c1set)
                fsd1 = frozenset(d1)
                fsd2 = frozenset(d2)
                atp = fsd1, fsd2
                self.atp_dict_unlinked[str(c1), str(c2)] = atp
        for atp in self.atp_dict_unlinked.keys():
            con_pairs = []
            tp = self.atp_dict_unlinked[atp]
            if tp in self.inverted_index_unlinked.keys():
                for y in self.inverted_index_unlinked[tp]:
                    con_pairs.append(y)
                con_pairs.append(atp)
                self.inverted_index_unlinked[tp] = con_pairs
            else:
                con_pairs.insert(0, atp)
                self.inverted_index_unlinked[tp] = con_pairs

    def detect_inconsistencies(self):
        """
        mismatch: dictionary for each ATP showing the list of linked and unlinked pairs belonging to it
        expanded_out: dictionary for each ATP-linked_pair-unlinked_pair tuple.
        :return:
        """
        today = date.today()
        mismatch = {}
        expanded_out = {}
        is_a_inference = {}
        for atp in self.inverted_index_unlinked:
            if atp in self.inverted_index_linked.keys():
                mismatch[atp] = {'a': self.inverted_index_linked[atp], 'b': self.inverted_index_unlinked[atp]}
        for inconsistency in mismatch.keys():
            alist = []
            blist = []
            alist = mismatch[inconsistency]['a']
            blist = mismatch[inconsistency]['b']
            for x, a in enumerate(alist):
                for y, b in enumerate(blist):
                    expanded_out[x, y, inconsistency] = {'Word Difference': inconsistency, 'C1 (Linked)': a[0],
                                                         'Label1': self.labeldict[a[0]]['label'], 'C2 (Linked)': a[1],
                                                         'Label2': self.labeldict[a[1]]['label'], 'C1 (Unlinked)': b[0],
                                                         'Label3': self.labeldict[b[0]]['label'], 'C2 (Unlinked)': b[1],
                                                         'Label4': self.labeldict[b[1]]['label']}
        df = pd.DataFrame(
            columns=['Word Difference', 'C1 (Linked)', 'Label1', 'C2 (Linked)', 'Label2', 'C1 (Unlinked)', 'Label3',
                     'C2 (Unlinked)', 'Label4'])
        for i, key in enumerate(expanded_out.keys()):
            C1 = expanded_out[key]['Word Difference']
            C2 = expanded_out[key]['C1 (Linked)']
            C3 = expanded_out[key]['Label1']
            C4 = expanded_out[key]['C2 (Linked)']
            C5 = expanded_out[key]['Label2']
            C6 = expanded_out[key]['C1 (Unlinked)']
            C7 = expanded_out[key]['Label3']
            C8 = expanded_out[key]['C2 (Unlinked)']
            C9 = expanded_out[key]['Label4']
            df.loc[i] = [C1, C2, C3, C4, C5, C6, C7, C8, C9]
        df.to_csv(f"expanded_output_{today}.csv")
        for i, diff in enumerate(mismatch.keys()):
            alist = []
            blist = []
            alist = mismatch[diff]['a']
            blist = mismatch[diff]['b']
            for b in blist:
                is_a_inference[diff, b] = {'Word Difference': diff, 'Unlinked Pair': b,
                                           'U_Label1': self.labeldict[b[0]]['label'],
                                           'U_Label2': self.labeldict[b[1]]['label'],
                                           'L_Label1': self.labeldict[alist[0][0]]['label'],
                                           'L_Label2': self.labeldict[alist[0][1]]['label'], 'Linked Pairs': alist}
        df1 = pd.DataFrame(columns=['Word Difference', 'Unlinked Pair', 'Linked Pairs'])
        for i, key in enumerate(is_a_inference.keys()):
            C1 = is_a_inference[key]['Word Difference']
            C2 = is_a_inference[key]['Unlinked Pair']
            C3 = is_a_inference[key]['Linked Pairs']
            df1.loc[i] = [C1, C2, C3]
        df1.to_csv(f"is_a_inconsistencies_{today}.csv")


file = "/Users/wmanuel3/OneDrive - The University of Texas Health Science Center at Houston/Education/Cui Labs/VO/ITP Recognition/VO.owl"
test1 = OntoReader(file)
test1.linked_methods()
test1.unlinked_methods("http://purl.obolibrary.org/obo/BFO_0000040")
test1.detect_inconsistencies()
