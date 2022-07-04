

def get_includes(args):
    includes = args.get('includes') or None
    if includes:
        includes = includes.replace(' ', '')
        includes = includes.split(',')
    return includes
    
def clean_dict(dict_obj:dict)-> dict:
    dict_obj = dict((k, v) for k, v in dict_obj.items() if v )
    return dict_obj

def clean_request_dict(dict_obj:dict)-> dict:
    dict_obj = dict((k, v) for k, v in dict_obj.items() if v is not None) 
    return dict_obj
    