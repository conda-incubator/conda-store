import base64
from typing import Dict, List, Optional

import pydantic
from sqlalchemy import tuple_
from sqlalchemy.orm import Query as SqlQuery


class Cursor(pydantic.BaseModel):
    last_id: Optional[int] = 1

    # List of names of attributes to order by, and the last value of the ordered attribute
    # {
    #   'namespace': 'foo',
    #   'environment': 'bar',
    # }
    last_value: Optional[Dict[str, str]] = {}

    def dump(self):
        return base64.b64encode(self.model_dump_json())

    @classmethod
    def load(cls, data: str):
        return cls.from_json(base64.b64decode(data))


def paginate(
    query: SqlQuery,
    cursor: Cursor,
    sort_by: List[str],
    valid_sort_by: Dict[str, object],
) -> SqlQuery:
    """Paginate the query using the cursor and the requested sort_bys.

    With cursor pagination, all keys used to order must be included in
    the call to query.filter().

    https://medium.com/@george_16060/cursor-based-pagination-with-arbitrary-ordering-b4af6d5e22db

    Parameters
    ----------
    query : SqlQuery
        Query containing database results to paginate
    cursor : Cursor
        Cursor object containing information about the last item
        on the previous page
    sort_by : List[str]
        List of sort_by query parameters
    valid_sort_by : Dict[str, object]
        Mapping between query parameter names and the orm object they apply to
    """
    objects = []
    last_values = []
    for obj in sort_by:
        objects.append(valid_sort_by[obj])
        last_values.append(cursor.last_value[obj])

    return query.filter(
        tuple_(*objects, object.id) > (*last_values, cursor.last_id)
    ).order_by(sorts)
