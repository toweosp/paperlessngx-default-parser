def get_parser(*args, **kwargs):
    from org_toweosp_paperlessngx_default_parser.parsers import DefaultDocumentParser

    return DefaultDocumentParser(*args, **kwargs)

def consumer_declaration(sender, **kwargs):
    """
    This parser handles documents of all mime types listed in /etc/mime.types
    """
    mimetype_defaultextension_map = {}

    with open('/etc/mime.types') as f:
        while input := f.readline():
            input = input.rstrip()
            if not input.startswith('#') and input.strip():
                mimetype,*other_columns = input.split('\t')
                extensions_column = list(filter(None, other_columns))

                default_extension = '.' + extensions_column[0].split(' ')[0] if extensions_column else ''
                
                mimetype_defaultextension_map[mimetype] = default_extension
        f.close()

    return {
        "parser": get_parser,
        # set weight to -1 so this parser has lower priority than the parsers provided by Paperless-ngx itself
        "weight": -1,
        "mime_types": mimetype_defaultextension_map,
    }
