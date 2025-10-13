from typing import cast, Literal

from nicegui.awaitable_response import AwaitableResponse
from nicegui.element import Element


class AgGrid(
    Element,
    component="aggrid.js",
    dependencies=["lib/aggrid/ag-grid-enterprise.min.js"],
    default_classes="nicegui-aggrid",
):
    license_key: str = None

    def __init__(
        self,
        options: dict,
        *,
        html_columns: list[int] = [],  # noqa: B006
        theme: str = "balham",
        auto_size_columns: bool = True,
    ) -> None:
        super().__init__()
        self._props["options"] = options
        self._props["html_columns"] = html_columns[:]
        self._props["auto_size_columns"] = auto_size_columns
        self._props["license_key"] = AgGrid.license_key
        self._classes.append(f"ag-theme-{theme}")

    @property
    def options(self) -> dict:
        """The options dictionary."""
        return self._props["options"]

    def update(self) -> None:
        super().update()
        self.run_method("update_grid")

    def run_grid_method(
        self, name: str, *args, timeout: float = 1
    ) -> AwaitableResponse:
        """Run an AG Grid API method.

        See `AG Grid API <https://www.ag-grid.com/javascript-data-grid/grid-api/>`_ for a list of methods.

        If the function is awaited, the result of the method call is returned.
        Otherwise, the method is executed without waiting for a response.

        :param name: name of the method
        :param args: arguments to pass to the method
        :param timeout: timeout in seconds (default: 1 second)

        :return: AwaitableResponse that can be awaited to get the result of the method call
        """
        return self.run_method("run_grid_method", name, *args, timeout=timeout)

    def run_row_method(
        self, row_id: str, name: str, *args, timeout: float = 1
    ) -> AwaitableResponse:
        """Run an AG Grid API method on a specific row.

        See `AG Grid Row Reference <https://www.ag-grid.com/javascript-data-grid/row-object/>`_ for a list of methods.

        If the function is awaited, the result of the method call is returned.
        Otherwise, the method is executed without waiting for a response.

        :param row_id: id of the row (as defined by the ``getRowId`` option)
        :param name: name of the method
        :param args: arguments to pass to the method
        :param timeout: timeout in seconds (default: 1 second)

        :return: AwaitableResponse that can be awaited to get the result of the method call
        """
        return self.run_method("run_row_method", row_id, name, *args, timeout=timeout)

    async def get_selected_rows(self) -> list[dict]:
        """Get the currently selected rows.

        This method is especially useful when the grid is configured with ``rowSelection: 'multiple'``.

        See `AG Grid API <https://www.ag-grid.com/javascript-data-grid/row-selection/#reference-selection-getSelectedRows>`_ for more information.

        :return: list of selected row data
        """  # noqa: E501
        result = await self.run_grid_method("getSelectedRows")
        return cast(list[dict], result)

    async def get_selected_row(self) -> dict | None:
        """Get the single currently selected row.

        This method is especially useful when the grid is configured with ``rowSelection: 'single'``.

        :return: row data of the first selection if any row is selected, otherwise `None`
        """
        rows = await self.get_selected_rows()
        return rows[0] if rows else None

    async def get_client_data(
        self,
        *,
        timeout: float = 1,
        method: Literal[
            "all_unsorted", "filtered_unsorted", "filtered_sorted", "leaf"
        ] = "all_unsorted",
    ) -> list[dict]:
        """Get the data from the client including any edits made by the client.

        This method is especially useful when the grid is configured with ``'editable': True``.

        See `AG Grid API <https://www.ag-grid.com/javascript-data-grid/accessing-data/>`_ for more information.

        Note that when editing a cell, the row data is not updated until the cell exits the edit mode.
        This does not happen when the cell loses focus, unless ``stopEditingWhenCellsLoseFocus: True`` is set.

        :param timeout: timeout in seconds (default: 1 second)
        :param method: method to access the data, "all_unsorted" (default), "filtered_unsorted", "filtered_sorted", "leaf"

        :return: list of row data
        """  # noqa: E501
        API_METHODS = {
            "all_unsorted": "forEachNode",
            "filtered_unsorted": "forEachNodeAfterFilter",
            "filtered_sorted": "forEachNodeAfterFilterAndSort",
            "leaf": "forEachLeafNode",
        }
        result = await self.client.run_javascript(
            f"""
            const rowData = [];
            getElement({self.id}).api.{API_METHODS[method]}(node => rowData.push(node.data));
            return rowData;
        """,
            timeout=timeout,
        )
        return cast(list[dict], result)

    async def load_client_data(self) -> None:
        """Obtain client data and update the element's row data with it.

        This syncs edits made by the client in editable cells to the server.

        Note that when editing a cell, the row data is not updated until the cell exits the edit mode.
        This does not happen when the cell loses focus, unless ``stopEditingWhenCellsLoseFocus: True`` is set.
        """
        client_row_data = await self.get_client_data()
        self.options["rowData"] = client_row_data
        self.update()
