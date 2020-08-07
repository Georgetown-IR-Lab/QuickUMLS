import spacy

import quickumls
from quickumls.spacy_component import SpacyQuickUMLS

# setup a spacy pipeline which includes QuickUMLS as a component and nothing else
nlp = spacy.load('en_core_web_sm')

nlp.remove_pipe('tagger')
nlp.remove_pipe('parser')

# TODO -- change this from a hard coded path to a small chunk of UMLS that can be legally distributed
quickumls_path = r'C:\temp_quickumls\SNOMED_RXNORM_CPT_lowercase'

threshold = 0.8

quickumls_component = SpacyQuickUMLS(nlp, quickumls_path, threshold = threshold)

nlp.add_pipe(quickumls_component)

doc = nlp('Pt c/o shortness of breath, chest pain, nausea, vomiting, diarrrhea')

for ent in doc.ents:
    print('Entity text : {}'.format(ent.text))
    print('Label : {}'.format(ent.label_))
    print('Similarity : {}'.format(ent._.similarity))
    print('Semtypes : {}'.format(ent._.semtypes))
    
print('DONE with spacy/QuickUMLS demo')