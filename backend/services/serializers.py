from bson import ObjectId


def serialize(document):
    """Convert MongoDB IDs into strings for JSON responses."""
    if document is None:
        return None
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    for key, value in list(result.items()):
        if isinstance(value, ObjectId):
            result[key] = str(value)
    return result
