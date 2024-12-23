from __future__ import annotations

import base64
import operator
from typing import Any

import pydantic
from fastapi import HTTPException
from sqlalchemy import asc, desc, tuple_
from sqlalchemy.orm import Query as SqlQuery
from sqlalchemy.sql.expression import ColumnClause


class Cursor(pydantic.BaseModel):
    last_id: int | None = 0
    count: int | None = None

    # List query parameters to order by, and the last value of the ordered attribute
    # {
    #   'namespace': 'foo',
    #   'environment': 'bar',
    # }
    last_value: dict[str, str] | None = {}

    def dump(self) -> str:
        return base64.b64encode(self.model_dump_json().encode("utf8"))

    @classmethod
    def load(cls, data: str | None = None) -> Cursor | None:
        if data is None:
            return None
        return cls.from_json(base64.b64decode(data).decode("utf8"))

    def get_last_values(self, order_names: list[str]) -> list[Any]:
        if order_names:
            return [self.last_value[name] for name in order_names]
        else:
            return []


def paginate(
    query: SqlQuery,
    ordering_metadata: OrderingMetadata,
    cursor: Cursor | None = None,
    order_by: list[str] | None = None,
    # valid_order_by: dict[str, str] | None = None,
    order: str = "asc",
    limit: int = 10,
) -> tuple[SqlQuery, Cursor]:
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
    valid_order_by : dict[str, str] | None
        Mapping between valid names to order by and the column names on the orm object they apply to
    cursor : Cursor | None
        Cursor object containing information about the last item on the previous page.
        If None, the first page is returned.
    order_by : list[str] | None
        List of sort_by query parameters

    Returns
    -------
    tuple[SqlQuery, Cursor]
        Query containing the paginated results, and Cursor for retrieving
        the next page
    """
    if order_by is None:
        order_by = []

    if order == "asc":
        comparison = operator.gt
        order_func = asc
    elif order == "desc":
        comparison = operator.lt
        order_func = desc
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid query parameter: order = {order}; must be one of ['asc', 'desc']",
        )

    # Get the python type of the objects being queried
    queried_type = query.column_descriptions[0]["type"]
    columns = ordering_metadata.get_requested_columns(order_by)

    # If there's a cursor already, use the last attributes to filter
    # the results by (*attributes, id) >/< (*last_values, last_id)
    # Order by desc or asc
    if cursor is not None:
        last_values = cursor.get_last_values(order_by)
        query = query.filter(
            comparison(
                tuple_(*columns, queried_type.id),
                (*last_values, cursor.last_id),
            )
        )

    breakpoint()
    query = query.order_by(
        *[order_func(col) for col in columns], order_func(queried_type.id)
    )
    data = query.limit(limit).all()
    count = query.count()

    if count > 0:
        last_result = data[-1]
        last_value = ordering_metadata.get_attr_values(last_result, order_by)

        next_cursor = Cursor(
            last_id=data[-1].id, last_value=last_value, count=query.count()
        )
    else:
        next_cursor = None

    return (data, next_cursor)


class CursorPaginatedArgs(pydantic.BaseModel):
    limit: int
    order: str
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
        order_names: list[str] | None = None,
        column_names: list[str] | None = None,
    ):
        self.order_names = order_names
        self.column_names = column_names

    def validate(self, model: Any):
        if len(self.order_names) != len(self.column_names):
            raise ValueError(
                "Each name of a valid ordering available to the order_by query parameter"
                "must have an associated column name to select in the table."
            )

        for col in self.column_names:
            if not hasattr(model, col):
                raise ValueError(f"No column named {col} found on model {model}.")

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
                idx = self.order_names.index(order_name)
                # columns.append(text(self.column_names[idx]))
                columns.append(self.column_names[idx])

        return columns

    def get_attr_values(
        self,
        obj: Any,
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
        breakpoint()
        values = {}
        for order_name in order_by:
            idx = self.order_names.index(order_name)
            attr = self.column_names[idx]
            values[order_name] = get_nested_attribute(obj, attr)

        return values


def get_nested_attribute(obj: Any, attr: str) -> Any:
    attribute, *rest = attr.split(".")
    while len(rest) > 0:
        obj = getattr(obj, attribute)
        attribute, *rest = rest

    return getattr(obj, attribute)
