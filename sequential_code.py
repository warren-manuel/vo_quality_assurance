from itertools import count
import time
import csv
import re
import pandas as pd
from urllib.request import AbstractDigestAuthHandler

# Parsing Ontology to variable
from owlready2 import *

location = "/Users/wmanuel3/OneDrive - The University of Texas Health Science Center at Houston/Education/Cui Labs/VO/ITP Recognition/VO.owl"
onto = get_ontology(location).load()

# Stop word recognizing
words = []
for i, c in enumerate(onto.classes()):
    name = str(c)
    text = str(c.label)
    print(text)
    specialChars = {"'", "(", ")", ","}
    for specialChar in specialChars:
        text = text.replace(specialChar, " ")
    text = str(text)[2:-2]
    w_list = (text.lower()).split()
    for word in w_list:
        words.append(word)
    print(i)

w_dict = {}
for word in words:
    if word in w_dict.keys():
        w_dict[word] += 1
    else:
        w_dict[word] = 1

"""
Extracting features from Ontology (name, ancestors)
Text formatting to remove " " and , from the string when multiple labels are present and to remove []
Passing the ancestors as a string into a set
"""

start = time.time()
labeldict = {}
anclist = {}
for i, c in enumerate(onto.classes()):
    name = str(c)
    text = str(c.label)
    print(text)
    specialChars = {"'", "(", ")", ","}
    for specialChar in specialChars:
        text = text.replace(specialChar, " ")
    text = str(text)[2:-2]
    labellist = set(text.lower().split())
    anc = set()
    for ancestor in c.ancestors(include_self=False):
        anc.add(str(ancestor))
    labeldict[name] = {'name': name, 'label': c.label, 'list': labellist, 'ancestors': anc}
    anclist[name] = anc
end = time.time()
print(end - start)
len(labeldict)

# Extracting Linked Concept pairs using ancestors
start = time.time()
x = 1
linked_con_pairs = set()
for c1 in anclist:
    for c2 in anclist[c1]:
        # print('RUN', x, c1, ' + ', c2, anclist[c1], file=linkeddic)
        linked_con_pairs.add((c1, c2))
        x = x + 1
end = time.time()
print(end - start)

# Extracting Unlinked Concept pairs ancestor list limited to a subroot only (changes made - or d1 in anclist[d2])
start = time.time()
unlinked_con_pairs_temp = {}
unlinked_con_pairs = set()
root = IRIS["http://purl.obolibrary.org/obo/BFO_0000040"]
for i, cls in enumerate(onto.get_children_of(root)):
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
                if d1 == d2 or d2 in anclist[d1] or d1 in anclist[d2] or labeldict[d1]['name'][0:6] != labeldict[d2][
                                                                                                           'name'][0:6]:
                    continue
                else:
                    unlinked_con_pairs.add((d1, d2))
    else:
        continue
end = time.time()
print(end - start)

# NEW - Inferring linked ITP based on if they have some common words.
start = time.time()
itp_dict_linked = {}
for c1, c2 in linked_con_pairs:
    c1set = set(labeldict[str(c1)]['list'])
    c2set = set(labeldict[str(c2)]['list'])
    if len(c2set.intersection(c1set)) != 0 and c1set != c2set:
        # Todo - Change this to  !=0
        d1 = c1set.difference(c2set)
        d2 = c2set.difference(c1set)
        fsd1 = frozenset(d1)
        fsd2 = frozenset(d2)
        itp = fsd1, fsd2
        itp_dict_linked[str(c1), str(c2)] = itp
end = time.time()
print(end - start)

start = time.time()
itp_dict_unlinked = {}
for c1, c2 in unlinked_con_pairs:
    c1set = set(labeldict[str(c1)]['list'])
    c2set = set(labeldict[str(c2)]['list'])
    if len(c2set.intersection(c1set)) != 0 and c1set != c2set:
        d1 = c1set.difference(c2set)
        d2 = c2set.difference(c1set)
        fsd1 = frozenset(d1)
        fsd2 = frozenset(d2)
        itp = fsd1, fsd2
        itp_dict_unlinked[str(c1), str(c2)] = itp
end = time.time()
print(end - start)

# Detecting inconsistencies
"""----------------------------------------------------------------------
Creating a inverted index - linked
This will insert the first occurrence of a concept pair (C1,C2) 
as the value for the inverted dict. 
inverted_ITP[d]=(C1,C2)
When the next concept pair (C3,C4) is found to have the same difference d
----------------------------------------------------------------------"""

start = time.time()
inverted_index_linked = {}
i = 0
for con_pair in itp_dict_linked.keys():
    con_pairs_list = []
    print(i)
    itp = itp_dict_linked[con_pair]
    if itp in inverted_index_linked.keys():
        print('OPTION 2')
        for y in inverted_index_linked[itp]:
            con_pairs_list.append(y)
        con_pairs_list.append(con_pair)
        inverted_index_linked[itp] = con_pairs_list
    else:
        con_pairs_list.insert(0, con_pair)
        inverted_index_linked[itp] = con_pairs_list
    i = i + 1
end = time.time()
print(end - start)

"""----------------------------------------------------------------------
Creating a inverted index - unlinked
----------------------------------------------------------------------"""

start = time.time()
inverted_index_unlinked = {}
i = 0
for itp in itp_dict_unlinked.keys():
    con_pairs = []
    print(i)
    tp = itp_dict_unlinked[itp]
    if tp in inverted_index_unlinked.keys():
        print('OPTION 2')
        for y in inverted_index_unlinked[tp]:
            con_pairs.append(y)
        con_pairs.append(itp)
        inverted_index_unlinked[tp] = con_pairs
    else:
        con_pairs.insert(0, itp)
        inverted_index_unlinked[tp] = con_pairs
    i = i + 1
end = time.time()
print(end - start)

# Aggregate inverted index by ATP
mismatch = {}
for i in inverted_index_unlinked:
    print(i)
    if i in inverted_index_linked.keys():
        mismatch[i] = {'a': inverted_index_linked[i], 'b': inverted_index_unlinked[i]}
len(mismatch)

finalout = {}
for i, diff in enumerate(mismatch.keys()):
    print(i)
    alist = []
    blist = []
    alist = mismatch[diff]['a']
    blist = mismatch[diff]['b']
    for x, a in enumerate(alist):
        for y, b in enumerate(blist):
            print("NEXT")
            finalout[x, y, diff] = {'Word Difference': diff, 'C1 (Linked)': a[0], 'Label1': labeldict[a[0]]['label'],
                                    'C2 (Linked)': a[1], 'Label2': labeldict[a[1]]['label'], 'C1 (Unlinked)': b[0],
                                    'Label3': labeldict[b[0]]['label'], 'C2 (Unlinked)': b[1],
                                    'Label4': labeldict[b[1]]['label']}

df = pd.DataFrame(
    columns=['Word Difference', 'C1 (Linked)', 'Label1', 'C2 (Linked)', 'Label2', 'C1 (Unlinked)', 'Label3',
             'C2 (Unlinked)', 'Label4'])
for i, key in enumerate(finalout.keys()):
    C1 = finalout[key]['Word Difference']
    C2 = finalout[key]['C1 (Linked)']
    C3 = finalout[key]['Label1']
    C4 = finalout[key]['C2 (Linked)']
    C5 = finalout[key]['Label2']
    C6 = finalout[key]['C1 (Unlinked)']
    C7 = finalout[key]['Label3']
    C8 = finalout[key]['C2 (Unlinked)']
    C9 = finalout[key]['Label4']
    df.loc[i] = [C1, C2, C3, C4, C5, C6, C7, C8, C9]

inference = {}
for i, diff in enumerate(mismatch.keys()):
    alist = []
    blist = []
    print(i)
    print(diff)
    print(mismatch[diff])
    alist = mismatch[diff]['a']
    blist = mismatch[diff]['b']
    for b in blist:
        inference[diff, b] = {'Word Difference': diff, 'Unlinked Pair': b, 'U_Label1': labeldict[b[0]]['label'],
                              'U_Label2': labeldict[b[1]]['label'], 'L_Label1': labeldict[alist[0][0]]['label'],
                              'L_Label2': labeldict[alist[0][1]]['label'], 'Linked Pairs': alist}
len(inference)

df1 = pd.DataFrame(
    columns=['Word Difference', 'Unlinked Pair', 'U_Label1', 'U_Label2', 'L_Label1', 'L_Label2', 'Linked Pairs'])
for i, key in enumerate(inference.keys()):
    C1 = inference[key]['Word Difference']
    C2 = inference[key]['Unlinked Pair']
    C3 = inference[key]['U_Label1']
    C4 = inference[key]['U_Label2']
    C5 = inference[key]['L_Label1']
    C6 = inference[key]['L_Label2']
    C7 = inference[key]['Linked Pairs']
    df1.loc[i] = [C1, C2, C3, C4, C5, C6, C7]

# ---------------------------- Outputs --------------------------
with open('inverted_index_unlinked.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in inverted_index_unlinked.items():
        writer.writerow([key, value])

with open('inverted_index_linked.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in inverted_index_linked.items():
        writer.writerow([key, value])

with open('mismatch2.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in mismatch.items():
        writer.writerow([key, value])

df1.to_csv('Inference_2022_03_19_01.csv')
len(df1)

df.to_csv('finaloutput_2022_03_19_01.csv')

# ---------------------------- Outputs --------------------------
