import spacy
from spacy.tokens import Span
from spacy.strings import StringStore

from .core import QuickUMLS
from . import constants

class SpacyQuickUMLS(object):
    name = 'QuickUMLS matcher'
    
    def __init__(self, nlp, quickumls_fp, best_match=True, ignore_syntax=False, **kwargs):
        """Instantiate SpacyQuickUMLS object

            This creates a QuickUMLS spaCy component which can be used in modular pipelines.  
            This module adds entity Spans to the document where the entity label is the UMLS CUI and the Span's "underscore" object is extended to contains "similarity" and "semtypes" for matched concepts.
            Note that this implementation follows and enforces a known spacy convention that entity Spans cannot overlap on a single token.

        Args:
            nlp: Existing spaCy pipeline.  This is needed to update the vocabulary with UMLS CUI values
            quickumls_fp (str): Path to QuickUMLS data
            best_match (bool, optional): Whether to return only the top match or all overlapping candidates. Defaults to True.
            ignore_syntax (bool, optional): Whether to use the heuristcs introduced in the paper (Soldaini and Goharian, 2016). TODO: clarify,. Defaults to False
            **kwargs: QuickUMLS keyword arguments (see QuickUMLS in core.py)
        """
        
        self.quickumls = QuickUMLS(quickumls_fp, 
            # By default, the QuickUMLS objects creates its own internal spacy pipeline but this is not needed
            # when we're using it as a component in a pipeline
            spacy_component = True,
            **kwargs)
        
        # save this off so that we can get vocab values of labels later
        self.nlp = nlp
        
        # keep these for matching
        self.best_match = best_match
        self.ignore_syntax = ignore_syntax

        # let's extend this with some proprties that we want
        Span.set_extension('similarity', default = -1.0)
        Span.set_extension('semtypes', default = -1.0)
        
    def __call__(self, doc):
        # pass in the document which has been parsed to this point in the pipeline for ngrams and matches
        matches = self.quickumls._match(doc, best_match=self.best_match, ignore_syntax=self.ignore_syntax)
        
        # NOTE: Spacy spans do not allow overlapping tokens, so we prevent the overlap here
        # For more information, see: https://github.com/explosion/spaCy/issues/3608
        tokens_in_ents_set = set()
        
        # let's track any other entities which may have been attached via upstream components
        for ent in doc.ents:
            for token_index in range(ent.start, ent.end):
                tokens_in_ents_set.add(token_index)
        
        # Convert QuickUMLS match objects into Spans
        for match in matches:
            # each match may match multiple ngrams
            for ngram_match_dict in match:
                start_char_idx = int(ngram_match_dict['start'])
                end_char_idx = int(ngram_match_dict['end'])
                
                cui = ngram_match_dict['cui']
                # add the string to the spacy vocab
                self.nlp.vocab.strings.add(cui)
                # pull out the value
                cui_label_value = self.nlp.vocab.strings[cui]
                
                # char_span() creates a Span from these character indices
                # UMLS CUI should work well as the label here
                span = doc.char_span(start_char_idx, end_char_idx, label = cui_label_value)
                
                # before we add this, let's make sure that this entity does not overlap any tokens added thus far
                candidate_token_indexes = set(range(span.start, span.end))
                
                # check the intersection and skip this if there is any overlap
                if len(tokens_in_ents_set.intersection(candidate_token_indexes)) > 0:
                    continue
                    
                # track this to make sure we do not introduce overlap later
                tokens_in_ents_set.update(candidate_token_indexes)
                
                # add some custom metadata to the spans
                span._.similarity = ngram_match_dict['similarity']
                span._.semtypes = ngram_match_dict['semtypes']
                doc.ents = list(doc.ents) + [span]
                
        return doc