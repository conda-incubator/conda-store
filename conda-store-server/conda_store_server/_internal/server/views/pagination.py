from __future__ import annotations

import base64
import operator
from enum import Enum
from typing import Any

import pydantic
from fastapi import HTTPException
from sqlalchemy import asc, desc, tuple_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm import Query as SqlQuery
from sqlalchemy.sql.expression import ColumnClause

from conda_store_server._internal.orm import Base


class Ordering(Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class Cursor(pydantic.BaseModel):
    last_id: int | None = 0

    # List query parameters to order by, and the last value of the ordered attribute
    # {
    #   'namespace': 'foo',
    #   'environment': 'bar',
    # }
    last_value: dict[str, str] | None = {}

    def dump(self) -> str:
        """Dump the cursor as a b64-encoded string.

        Returns
        -------
        str
            base64-encoded string containing the information needed
            to retrieve the page of data following the location of the cursor
        """
        return base64.b64encode(self.model_dump_json().encode("utf8"))

    @classmethod
    def load(cls, b64_cursor: str | None = None) -> Cursor:
        """Create a Cursor from  a b64-encoded string.

        Parameters
        ----------
        b64_cursor : str | None
            base64-encoded string containing information about the cursor

        Returns
        -------
        Cursor
            Cursor representation of the b64-encoded string
        """
        if b64_cursor is None:
            return cls(last_id=None, last_value=None)
        return cls.model_validate_json(base64.b64decode(b64_cursor).decode("utf8"))

    def get_last_values(self, order_names: list[str]) -> list[Any]:
        """Get a list of the values corresponding to the order_names.

        Parameters
        ----------
        order_names : list[str]
            List of names of values stored in the cursor

        Returns
        -------
        list[Any]
            The last values pointed to by the cursor for the given order_names
        """
        if order_names:
            return [self.last_value[name] for name in order_names]
        else:
            return []

    @classmethod
    def end(cls) -> Cursor:
        """Cursor representing the end of a set of paginated results.

        Returns
        -------
        Cursor
            An empty cursor
        """
        return cls(last_id=None, last_value=None)

    @classmethod
    def begin(cls) -> Cursor:
        """Cursor representing the beginning of a set of paginated results.

        Returns
        -------
        Cursor
            A cursor that points at the first result; the count is 0
            because this cursor
        """
        return cls(last_id=0, last_value=None)


def paginate(
    query: SqlQuery,
    ordering_metadata: OrderingMetadata,
    cursor: Cursor | None = None,
    sort_by: list[str] | None = None,
    order: Ordering = Ordering.ASCENDING,
    limit: int = 10,
) -> tuple[list[Base], Cursor, int]:
    """Paginate the query using the cursor and the requested sort_bys.

    This function assumes that the first column of the query contains
    the type whose ID should be used to sort the results.

    Additionally, with cursor pagination all keys used to order the results
    must be included in the call to query.filter().

    https://medium.com/@george_16060/cursor-based-pagination-with-arbitrary-ordering-b4af6d5e22db

    Parameters
    ----------
    query : SqlQuery
        Query containing database results to paginate
    cursor : Cursor | None
        Cursor object containing information about the last item on the previous page.
        If None, the first page is returned.
    order_by : list[str] | None
        List of query parameters to order the results by

    Returns
    -------
    tuple[Base, Cursor, int]
        Query containing the paginated results, Cursor for retrieving
        the next page, and total number of results
    """
    if sort_by is None:
        sort_by = []

    if order == Ordering.ASCENDING:
        comparison = operator.gt
        order_func = asc
    elif order == Ordering.DESCENDING:
        comparison = operator.lt
        order_func = desc
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot order results: {order}"
                f"Valid order values are [{Ordering.ASCENDING.value}, {Ordering.DESCENDING.value}]",
            ),
        )

    invalid_params = ordering_metadata.get_invalid_orderings(sort_by)
    if invalid_params:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot sort results by {invalid_params}. "
                f"Valid sort_by values are {ordering_metadata.valid_orderings}"
            ),
        )

    # Fetch the total number of objects in the database before filtering
    count = query.count()

    # Get the python type of the objects being queried
    queried_type = query.column_descriptions[0]["type"]
    columns = ordering_metadata.get_requested_columns(sort_by)

    # If there's a cursor already, use the last attributes to filter
    # the results by (*attributes, id) >/< (*last_values, last_id)
    # Order by desc or asc
    if cursor is not None and cursor != Cursor.end():
        last_values = cursor.get_last_values(sort_by)
        query = query.filter(
            comparison(
                tuple_(*columns, queried_type.id),
                (*last_values, cursor.last_id),
            )
        )

    # Order the query by the requested columns, and also by the object's primary key
    query = query.order_by(
        *([order_func(col) for col in columns] + [order_func(queried_type.id)])
    )
    data = query.limit(limit).all()

    if len(data) > 0:
        last_result = data[-1]
        next_cursor = Cursor(
            last_id=last_result.id,
            last_value=ordering_metadata.get_attr_values(last_result, sort_by),
        )
    else:
        next_cursor = Cursor.end()

    return (data, next_cursor, count)


class CursorPaginatedArgs(pydantic.BaseModel):
    limit: int | None
    order: Ordering
    sort_by: list[str]

    @pydantic.field_validator("sort_by")
    def validate_sort_by(cls, v: list[str]) -> list[str]:
        """Validate the columns to sort by.

        FastAPI doesn't support lists in query parameters, so if the
        `sort_by` value is a single-element list, assume that this
        could be a comma-separated list. No harm in attempting to split
        this by commas.

        Parameters
        ----------
        v : list[str]


        Returns
        -------
        list[str]
        """
        if len(v) == 1:
            v = v[0].split(",")
        return v


class OrderingMetadata:
    def __init__(
        self,
        valid_orderings: list[str] | None = None,
        column_names: list[str] | None = None,
        column_objects: list[InstrumentedAttribute] | None = None,
    ):
        self.valid_orderings = valid_orderings
        self.column_names = column_names
        self.column_objects = column_objects

    def get_invalid_orderings(self, query_params: list[str] | None) -> list[str]:
        """Return a list of invalid ordering query parameters.

        Parameters
        ----------
        query_params : list[str] | None
            A list of ordering query parameters

        Returns
        -------
        list[str]
            A list of the query parameters which cannot be used to order the results
        """
        if query_params is None:
            return []

        return [param for param in query_params if param not in self.valid_orderings]

    def get_requested_columns(
        self,
        order_by: list[str] | None = None,
    ) -> list[ColumnClause]:
        """Get a list of sqlalchemy columns requested by the value of the order_by query param.

        Parameters
        ----------
        order_by : list[str] | None
            If specified, this should be a subset of self.order_names. If none, an
            empty list is returned.

        Returns
        -------
        list[ColumnClause]
            A list of sqlalchemy columns corresponding to the order_by values passed
            as a query parameter
        """
        columns = []
        if order_by:
            for order_name in order_by:
                idx = self.valid_orderings.index(order_name)
                columns.append(self.column_objects[idx])

        return columns

    def __str__(self) -> str:
        return f"OrderingMetadata<order_names={self.valid_orderings}, column_names={self.column_names}>"

    def __repr__(self) -> str:
        return str(self)

    def get_attr_values(
        self,
        obj: Base,
        order_by: list[str] | None = None,
    ) -> dict[str, Any]:
        """Using the order_by values, get the corresponding attribute values on obj.

        Parameters
        ----------
        obj : Any
            sqlalchemy model containing attribute names that are contained in
            `self.column_names`
        order_by : list[str] | None
            Values that the user wants to order by; these are used to look up the corresponding
            column names that are used to access the attributes of `obj`.

        Returns
        -------
        dict[str, Any]
            A mapping between the `order_by` values and the attribute values on `obj`

        """
        values = {}
        for order_name in order_by:
            idx = self.valid_orderings.index(order_name)
            attr = self.column_names[idx]
            values[order_name] = get_nested_attribute(obj, attr)

        return values


def get_nested_attribute(obj: Base, attr: str) -> str | int | float:
    """Get a nested attribute from the given sqlalchemy model.

    Parameters
    ----------
    obj : Base
        A sqlalchemy model for which a (possibly nested) attribute is to be
        retrieved
    attr : str
        String attribute; nested attributes should be separated with `.`

    Returns
    -------
    str | int | float
        Value of the attribute; strictly this can be any column type supported
        by sqlalchemy, but for conda-store this is a str, an int, or a float

    Examples
    --------
    >>> env = db.query(orm.Environment).join(orm.Namespace).first()
    >>> get_nested_attribute(env, 'namespace.name')
    'namespace1'
    >>> get_nested_attribute(env, 'name')
    'my_environment'
    """
    attribute, *rest = attr.split(".")
    while len(rest) > 0:
        obj = getattr(obj, attribute)
        attribute, *rest = rest

    return getattr(obj, attribute)
