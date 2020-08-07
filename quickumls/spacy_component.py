import spacy
from spacy.tokens import Span
from spacy.strings import StringStore

from .core import QuickUMLS
from . import constants

class SpacyQuickUMLS(object):
    name = 'QuickUMLS matcher'
    
    def __init__(self, nlp, quickumls_path, 
        # these are all params that were from match() in quickumls but since we want to construct this
        # and then make its behavior consistent as a component, we'll set them here:
        best_match = True, ignore_syntax = False, verbose = False,
        # these below are the same as in quickumls.py (so let's pass them through as our wrapper)
        overlapping_criteria='score', threshold=0.7, window=5,
        similarity_name='jaccard', min_match_length=3,
        accepted_semtypes=constants.ACCEPTED_SEMTYPES):
        
        self.quickumls = QuickUMLS(quickumls_path, 
            overlapping_criteria=overlapping_criteria, threshold=threshold, window=window,
            similarity_name=similarity_name, min_match_length=min_match_length,
            accepted_semtypes=accepted_semtypes,
            # By default, the QuickUMLS objects creates its own internal spacy pipeline but we do not need that in this case
            spacy_component = True,
            verbose = verbose)
        
        # save this off so that we can get vocab values of labels later
        self.nlp = nlp
        
        self.best_match = best_match
        self.ignore_syntax = ignore_syntax
        self.verbose = verbose

        # let's extend this with some proprties that we want
        Span.set_extension('similarity', default = -1.0)
        Span.set_extension('semtypes', default = -1.0)
        
        if self.verbose:
            print('Accepted semtypes : [{0}]'.format(accepted_semtypes))
        
    def __call__(self, doc):
        # much of this is a re-write of match() in quickumls.py
        # however, the changes include:
        # receiving an incoming doc (rather than parsing at calling time)
        # transforming matches into Spans as per spaCy custom Entity code example
        
        ngrams = None
        # pass in the incoming doc which has already been tokenized (ready for ngrams)
        if self.ignore_syntax:
            ngrams = self.quickumls._make_token_sequences(doc)
        else:
            ngrams = self.quickumls._make_ngrams(doc)
            
        # perform the matching
        matches = self.quickumls._get_all_matches(ngrams)
        
        if self.verbose:
            print('Total matches before best match: [{0}]'.format(len(matches)))
        
        if self.best_match:
            matches = self.quickumls._select_terms(matches)
            
            if self.verbose:
                print('Total matches after best match: [{0}]'.format(len(matches)))
            
        self.quickumls._print_verbose_status(doc, matches)
        
        # Here's another change: convert match objects into Spans
        for match in matches:
            # each match may match multiple ngrams
            for ngram_match_dict in match:
                start_char_idx = int(ngram_match_dict['start'])
                end_char_idx = int(ngram_match_dict['end'])
                
                cui = ngram_match_dict['cui']
                # add the string
                self.nlp.vocab.strings.add(cui)
                # pull out the value
                cui_label_value = self.nlp.vocab.strings[cui]
                
                # char_span() created a Span from the character indices
                # UMLS CUI should work well as the label here
                span = doc.char_span(start_char_idx, end_char_idx, label = cui_label_value)
                # add some custom metadata
                span._.similarity = ngram_match_dict['similarity']
                span._.semtypes = ngram_match_dict['semtypes']
                doc.ents = list(doc.ents) + [span]
                
        return doc