#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Saga Inc.
# Distributed under the terms of the GPL License.
from copy import deepcopy
from time import perf_counter
from typing import Any, Dict, List, Optional, Set, Tuple
from mitosheet.code_chunks.code_chunk import CodeChunk
from mitosheet.code_chunks.step_performers.sort_code_chunk import SortCodeChunk

from mitosheet.state import State
from mitosheet.step_performers.step_performer import StepPerformer
from mitosheet.errors import (
    make_invalid_sort_error
)
from mitosheet.transpiler.transpile_utils import column_header_to_transpiled_code
from mitosheet.types import ColumnID

# CONSTANTS USED IN THE SORT STEP ITSELF
SORT_DIRECTION_ASCENDING = 'ascending'
SORT_DIRECTION_DESCENDING = 'descending'
SORT_DIRECTION_NONE = 'none'

class SortStepPerformer(StepPerformer):
    """
    Allows you to sort a df based on key column, in either
    ascending or descending order.
    """

    @classmethod
    def step_version(cls) -> int:
        return 2

    @classmethod
    def step_type(cls) -> str:
        return 'sort'
    
    @classmethod
    def saturate(cls, prev_state: State, params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    @classmethod
    def execute( # type: ignore
        cls,
        prev_state: State,
        sheet_index: int,
        column_id: ColumnID,
        sort_direction: str,
        **params
    ) -> Tuple[State, Optional[Dict[str, Any]]]:
        """
        Returns the new new post state after sorting the sheet
        at `sheet_index` by the passed `column_id` in the given
        `sort_direction`
        """

        column_header = prev_state.column_ids.get_column_header_by_id(sheet_index, column_id)

        # We make a new state to modify it
        post_state = prev_state.copy(deep_sheet_indexes=[sheet_index])

        try: 
            pandas_start_time = perf_counter()
            if sort_direction != SORT_DIRECTION_NONE:
                new_df = prev_state.dfs[sheet_index].sort_values(by=column_header, ascending=(sort_direction == SORT_DIRECTION_ASCENDING), na_position=('first' if sort_direction == SORT_DIRECTION_ASCENDING else 'last'))
            else:
                # We notably let the user sort by the "none" direction, which effectively allows the user
                # to unapply the sort by toggling the sort button after they click it once
                new_df = prev_state.dfs[sheet_index]
            
            pandas_processing_time = perf_counter() - pandas_start_time
            post_state.dfs[sheet_index] = new_df
        except TypeError as e:
            # A NameError occurs when you try to sort a column with incomparable 
            # dtypes (ie: a column with strings and floats)
            print(e)
            # Generate an error informing the user
            raise make_invalid_sort_error(column_header)

        return post_state, {
            'pandas_processing_time': pandas_processing_time
        }

    @classmethod
    def transpile(
        cls,
        prev_state: State,
        post_state: State,
        params: Dict[str, Any],
        execution_data: Optional[Dict[str, Any]],
    ) -> List[CodeChunk]:
        return [
            SortCodeChunk(prev_state, post_state, params, execution_data)
        ]

    @classmethod
    def get_modified_dataframe_indexes( # type: ignore
        cls, 
        sheet_index: int,
        column_id: ColumnID,
        sort_direction: str,
        **params
    ) -> Set[int]:
        return {sheet_index}