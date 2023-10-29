class RestFilter:
    """ filter result objects and related objects (e.g. employee.courses) """

    def get_includes(self, args):
        """ returns included related objects passed in query string [?includes=something,something] """
        includes = args.get('includes') or None
        if includes:
            includes = includes.replace(' ', '')
            includes = includes.split(',')
        return includes

    def clean_dict(self, dict_obj: dict) -> dict:
        """ removes empty values from a dict """
        if not dict_obj:
            return dict_obj
        return dict((k, v) for k, v in dict_obj.items() if v)

    def clean_request_dict(self, dict_obj: dict) -> dict:
        """ removes empty values from a dict """
        dict_obj = dict((k, v) for k, v in dict_obj.items() if v is not None)
        return dict_obj
