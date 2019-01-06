try:
    from quickumls import QuickUMLS
except ImportError:
    from .quickumls import QuickUMLS

print('Creating QuickUMLS object...')
    
quickumls_path = r'C:\quickumls'
    
matcher = QuickUMLS(quickumls_path)

print('QuickUMLS object created...')

text = "The ulna has dislocated posteriorly from the trochlea of the humerus."

print('*************************')
print('Text:')
print(text)
print('*************************')

res = matcher.match(text, best_match=True, ignore_syntax=False)

print('Matching results:')
print(res)

