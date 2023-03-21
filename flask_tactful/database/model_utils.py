from sqlalchemy import inspect
from sqlalchemy.ext.declarative import as_declarative


def model_to_dict(obj, include_relationships=None, recursive_relationship=None):
    """converts a model to dict, it can also handled related items, just specify a list of related items include_relationships=["related_attr_name"]

    Args:
        obj (_type_): _description_
        include_relationships (_type_, optional): _description_. Defaults to None.
        recursive_relationship (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    # print([c.key for c in inspect(obj).mapper.column_attrs])
    model_class = type(obj)
    # Models with __protected__ list, this function will skip these columns because they might contain sensitive data (like passwords)
    masked = model_class.__masked__ if hasattr(model_class, "__masked__") else []
    ret = {}
    for c in inspect(obj).mapper.column_attrs:
        if c.key not in masked:
            ret[c.key] = getattr(obj, c.key)
            # print("output {0} = {1}".format(c.key, getattr(obj, c.key)))
    if include_relationships:
        for relationship in inspect(type(obj)).relationships:
            if relationship.key in include_relationships:
                # print("relation: ", relationship.key)

                related = getattr(obj, relationship.key)
                if relationship.uselist and related is not None:
                    ret[relationship.key] = [model_to_dict(r, recursive_relationship) for r in related]
                elif related is not None:
                    ret[relationship.key] = model_to_dict(related, recursive_relationship)

    return ret


def model_from_dict(model, **kwargs):
    """ loads model data from input dict, does not handle related items
        it is better than model.__init__() because it ignores non existing keys while init crashes if a non existing item is sent

    Args:
        model (_type_): _description_
    """
    protected = model.__protected__ if hasattr(model, "__protected__") else []
    for key, value in kwargs.items():
        if key not in protected:
            if hasattr(model, key):
                # print("setting {0}= {1}".format(key, value))
                setattr(model, key, value)
        else:
            print("NOT setting {0} not found (value={1})".format(key, value))


# commented by Fouad, deprecated in Sqlalchemy v2.0
# # adds as_dict function to any model, note this does not handle relationships
# @as_declarative()
# class Base:
#     def as_dict(self):
#         return {c.key: getattr(self, c.key)
#                 for c in inspect(self).mapper.column_attrs}


def walk_model_relations(obj):
    """ walks model relatonships recursively, might not be useful because it can walk to parent relations too (profile for user.profile)
        so it can build the whole relationship graph


    Args:
        obj (_type_): _description_

    Yields:
        _type_: _description_
    """
    deque = [obj]

    seen = set()

    while deque:
        obj = deque.pop(0)
        if obj in seen:
            continue
        else:
            seen.add(obj)
            yield obj
        insp = inspect(obj)
        for relationship in insp.mapper.relationships:
            related = getattr(obj, relationship.key)
            if relationship.uselist:
                deque.extend(related)
            elif related is not None:
                deque.append(related)
