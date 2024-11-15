import base64

import pydantic
from sqlalchemy import tuple_
from sqlalchemy.orm import Query as SqlQuery


class Cursor(pydantic.BaseModel):
    last_id: int | None = 1

    # List of names of attributes to order by, and the last value of the ordered attribute
    # {
    #   'namespace': 'foo',
    #   'environment': 'bar',
    # }
    last_value: dict[str, str] | None = {}

    def dump(self):
        return base64.b64encode(self.model_dump_json())

    @classmethod
    def load(cls, data: str | None = None):
        if data is None:
            return cls()
        return cls.from_json(base64.b64decode(data))


def paginate(
    query: SqlQuery,
    cursor: Cursor,
    sort_by: list[str] | None = None,
    valid_sort_by: dict[str, object] | None = None,
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
    sort_by : list[str] | None
        List of sort_by query parameters
    valid_sort_by : dict[str, object] | None
        Mapping between query parameter names and the orm object they apply to
    """
    breakpoint()

    if sort_by is None:
        sort_by = []

    if valid_sort_by is None:
        valid_sort_by = {}

    objects = []
    last_values = []
    for obj in sort_by:
        objects.append(valid_sort_by[obj])
        last_values.append(cursor.last_value[obj])

    return query.filter(
        tuple_(*objects, object.id) > (*last_values, cursor.last_id)
    )  # .order_by(sorts)
