#beautify description in swagger documentation

def desc(txt=""):
    """ highlight description """
    return f"<h3>{txt}</h3>"

def header(txt,cases=None):
    """ highlight header """
    return f"<h1>{txt}</h1><br> + {usecases(cases)}"

def usecases(cases):
    """ highlight usecase """
    return "<br>".join([desc(usecase) for usecase in cases]) if cases else ""

def namespace_doc(description,cases=None):
    """ highlight namespace description """
    return f"<h2>{description}</h2><br> {usecases(cases)}"
    
def responses_doc(exceptions,custom_exceptions=None):
    """ highlight response documentation """
    res = {}
    for exception in exceptions:
        res[exception.code] = desc(exception.description)
    if custom_exceptions:
        for exception in custom_exceptions:
            res[exception] = desc(custom_exceptions[exception])
    return res

def path_ids_doc(path_params):
    """ highlight path paremeters """
    res = {}
    for param in path_params:
        res[param]={'name': param, 'in': 'path', 'type': 'integer', 'required': True, 'description': 'The '+param+' identifier'}
    return res
