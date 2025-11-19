from ..utils.books import BOOKS_3LTR

def parse_to_tokens(raw_files, spec):
    return [], {'books': spec.get('books') or BOOKS_3LTR, 'token_count': 0}
