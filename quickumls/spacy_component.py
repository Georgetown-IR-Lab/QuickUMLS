from spacy.language import Language
from spacy.tokens import Doc, Span

from .core import QuickUMLS


@Language.factory("quickumls", default_config={"options": {}})
def create_quickumls(nlp, name, quickumls_fp, options):
    return SpacyQuickUMLS(nlp, quickumls_fp, **options)


class SpacyQuickUMLS(object):
    """Add UMLS entities to a pipeline and expose candidate groups on doc._.quickumls."""
    name = 'QuickUMLS matcher'

    def __init__(self, nlp, quickumls_fp, best_match=True, ignore_syntax=False, **kwargs):
        for cls, name, default in ((Doc, 'quickumls', None), (Span, 'similarity', -1.0),
                                   (Span, 'semtypes', -1.0)):
            if not cls.has_extension(name):
                cls.set_extension(name, default=default)
            elif cls.get_extension(name) != (default, None, None, None):
                raise ValueError(f"Incompatible spaCy extension: {cls.__name__}._.{name}")
        self.nlp = nlp
        self.quickumls = QuickUMLS(quickumls_fp, spacy_component=True, **kwargs)
        self.best_match = best_match
        self.ignore_syntax = ignore_syntax

    def __call__(self, doc):
        entities = list(doc.ents)
        groups = self.quickumls._match(doc, best_match=False, ignore_syntax=self.ignore_syntax)
        selected = self.quickumls._select_terms(groups, ((e.start_char, e.end_char) for e in entities))
        doc._.quickumls = selected if self.best_match else groups
        for group in selected:
            top = group[0]
            span = doc.char_span(top['start'], top['end'], label=top['cui'])
            if span is not None:
                span._.similarity = top['similarity']
                span._.semtypes = top['semtypes']
                entities.append(span)
        doc.ents = entities
        return doc
