#beautify description in swagger documentation

def desc(txt=""):
    return "<h3>{0}</h3>".format(txt)
def header(txt,cases=None):
    return "<h1>{0}</h1><br>".format(txt)+usecases(cases)
def usecases(cases):
    return "<br>".join([desc(usecase) for usecase in cases]) if cases else ""
def namespace_doc(description,cases=None):
    return "<h2>{0}</h2><br>".format(description)+usecases(cases)
    
def responses_doc(exceptions,custom_exceptions=None):
    res = {}
    for exception in exceptions:
        res[exception.code] = desc(exception.description)
    if custom_exceptions:
        for exception in custom_exceptions:
            res[exception] = desc(custom_exceptions[exception])
    return res

def path_ids_doc(path_params):
    res = {}
    for param in path_params:
        res[param]={'name': param, 'in': 'path', 'type': 'integer', 'required': True, 'description': 'The '+param+' identifier'}
    return res
