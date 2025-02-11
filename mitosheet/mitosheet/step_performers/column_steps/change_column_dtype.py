#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Saga Inc.
# Distributed under the terms of the GPL License.
from copy import copy
from time import perf_counter
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
from mitosheet.code_chunks.code_chunk import CodeChunk
from mitosheet.code_chunks.step_performers.column_steps.change_column_dtype_code_chunk import ChangeColumnDtypeCodeChunk
from mitosheet.code_chunks.step_performers.column_steps.refresh_dependant_columns_code_chunk import RefreshDependantColumnsCodeChunk

from mitosheet.errors import get_recent_traceback, make_invalid_column_type_change_error
from mitosheet.sheet_functions.types import to_int_series
from mitosheet.sheet_functions.types.to_boolean_series import to_boolean_series
from mitosheet.sheet_functions.types.to_float_series import to_float_series
from mitosheet.sheet_functions.types.to_timedelta_series import \
    to_timedelta_series
from mitosheet.sheet_functions.types.utils import (get_datetime_format,
                                                   is_bool_dtype,
                                                   is_datetime_dtype,
                                                   is_float_dtype,
                                                   is_int_dtype,
                                                   is_string_dtype,
                                                   is_timedelta_dtype)
from mitosheet.state import FORMAT_DEFAULT, State
from mitosheet.step_performers.column_steps.set_column_formula import (
    refresh_dependant_columns)
from mitosheet.step_performers.step_performer import StepPerformer
from mitosheet.types import ColumnID


class ChangeColumnDtypeStepPerformer(StepPerformer):
    """"
    A step that allows changing the dtype of a column to a different
    dtype.

    Currently, supports: 'bool', 'int', 'float', 'str', 'datetime', 'timedelta'
    """

    @classmethod
    def step_version(cls) -> int:
        return 2

    @classmethod
    def step_type(cls) -> str:
        return 'change_column_dtype'

    @classmethod
    def saturate(cls, prev_state: State, params: Dict[str, Any]) -> Dict[str, Any]:
        sheet_index = params['sheet_index']
        column_id = params['column_id']
        column_header = prev_state.column_ids.get_column_header_by_id(sheet_index, column_id)
        params['old_dtype'] = str(prev_state.dfs[sheet_index][column_header].dtype)
        return params

    @classmethod
    def execute( # type: ignore
        cls,
        prev_state: State,
        sheet_index: int,
        column_id: ColumnID,
        old_dtype: str,
        new_dtype: str,
        **params
    ) -> Tuple[State, Optional[Dict[str, Any]]]:
        # Create the post state
        post_state = prev_state.copy(deep_sheet_indexes=[sheet_index])

        column_header = prev_state.column_ids.get_column_header_by_id(sheet_index, column_id)
        
        column: pd.Series = prev_state.dfs[sheet_index][column_header]
        new_column = column
        
        # How we handle the type conversion depends on what type it is
        try:
            pandas_start_time = perf_counter()
            if is_bool_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    pass
                elif is_int_dtype(new_dtype):
                    new_column = new_column.astype('int')
                elif is_float_dtype(new_dtype):
                    new_column = column.astype('float')
                elif is_string_dtype(new_dtype):
                    new_column = column.astype('str')
                elif is_datetime_dtype(new_dtype):
                    raise make_invalid_column_type_change_error(
                        column_header,
                        old_dtype,
                        new_dtype
                    )
                elif is_timedelta_dtype(new_dtype):
                    raise make_invalid_column_type_change_error(
                        column_header,
                        old_dtype,
                        new_dtype
                    )
            if is_int_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    new_column = column.fillna(False).astype('bool')
                elif is_int_dtype(new_dtype):
                    pass
                elif is_float_dtype(new_dtype):
                    new_column = column.astype('float')
                elif is_string_dtype(new_dtype):
                    new_column = column.astype('str')
                elif is_datetime_dtype(new_dtype):
                    new_column = pd.to_datetime(
                        column, 
                        unit='s',
                        errors='coerce'
                    )
                elif is_timedelta_dtype(new_dtype):
                    new_column = to_timedelta_series(column)
            elif is_float_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    new_column = column.fillna(False).astype('bool')
                elif is_int_dtype(new_dtype):
                    new_column = column.fillna(0).astype('int')
                elif is_float_dtype(new_dtype):
                    pass
                elif is_string_dtype(new_dtype):
                    new_column = column.astype('str')
                elif is_datetime_dtype(new_dtype):
                    new_column = pd.to_datetime(
                        column, 
                        unit='s',
                        errors='coerce'
                    )
                elif is_timedelta_dtype(new_dtype):
                    new_column = to_timedelta_series(column)
            elif is_string_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    new_column = to_boolean_series(new_column)
                elif is_int_dtype(new_dtype):
                    new_column = to_int_series(column)
                elif is_float_dtype(new_dtype):
                    new_column = to_float_series(column)
                elif is_string_dtype(new_dtype):
                    pass
                elif is_datetime_dtype(new_dtype):
                    # Guess the datetime format to the best of Pandas abilities
                    datetime_format = get_datetime_format(column)
                    # If it's None, then infer_datetime_format is enough to figure it out
                    if datetime_format is not None:
                        new_column = pd.to_datetime(
                            column,
                            format=datetime_format,
                            errors='coerce'
                        )
                    else:
                        new_column = pd.to_datetime(
                            column,
                            infer_datetime_format=True,
                            errors='coerce'
                        )
                elif is_timedelta_dtype(new_dtype):
                    new_column = to_timedelta_series(column)
            elif is_datetime_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    new_column = ~column.isnull()
                elif is_int_dtype(new_dtype):
                    new_column = column.astype('int') / 10**9
                elif is_float_dtype(new_dtype):
                    # For some reason, we have to do all the conversions at once
                    new_column = column.astype('int').astype('float') / 10**9
                elif is_string_dtype(new_dtype):
                    # NOTE: this is the same conversion that we send to the frontend
                    new_column = column.dt.strftime('%Y-%m-%d %X')
                elif is_datetime_dtype(new_dtype):
                    pass
                elif is_timedelta_dtype(new_dtype):
                    raise make_invalid_column_type_change_error(
                        column_header,
                        old_dtype,
                        new_dtype
                    )
            elif is_timedelta_dtype(old_dtype):
                if is_bool_dtype(new_dtype):
                    new_column = ~column.isnull()
                elif is_int_dtype(new_dtype):
                    new_column = column.dt.total_seconds().astype('int')
                elif is_float_dtype(new_dtype):
                    new_column = column.dt.total_seconds()
                elif is_string_dtype(new_dtype):
                    new_column = column.astype('str')
                elif is_datetime_dtype(new_dtype):
                    raise make_invalid_column_type_change_error(
                        column_header,
                        old_dtype,
                        new_dtype
                    )
                elif is_timedelta_dtype(new_dtype):
                    pass

            # We update the column, as well as the type of the column
            post_state.dfs[sheet_index][column_header] = new_column
            pandas_processing_time = perf_counter() - pandas_start_time

            # If we're changing between number columns, we keep the formatting on the column. Otherwise, we remove it
            if not ((is_int_dtype(old_dtype) or is_float_dtype(old_dtype)) and (is_int_dtype(new_dtype) or is_float_dtype(new_dtype))):
                post_state.column_format_types[sheet_index][column_id] = {'type': FORMAT_DEFAULT}
                
            refresh_dependant_columns(post_state, post_state.dfs[sheet_index], sheet_index, column_id)

            return post_state, {
                'pandas_processing_time': pandas_processing_time
            }
        except:
            print(get_recent_traceback())
            raise make_invalid_column_type_change_error(
                column_header,
                old_dtype,
                new_dtype
            )
        

    @classmethod
    def transpile(
        cls,
        prev_state: State,
        post_state: State,
        params: Dict[str, Any],
        execution_data: Optional[Dict[str, Any]],
    ) -> List[CodeChunk]:
        return [
            ChangeColumnDtypeCodeChunk(prev_state, post_state, params, execution_data),
            # Note that we also refresh all the dependant columns, starting with the set cell value
            RefreshDependantColumnsCodeChunk(
                prev_state, 
                post_state, 
                # We construct the params for this CodeChunk as well
                {
                    'sheet_index': params['sheet_index'],
                    'column_id': params['column_id'],
                }, 
                None
            )
        ]

    @classmethod
    def get_modified_dataframe_indexes( # type: ignore
        cls, 
        sheet_index: int,
        column_id: ColumnID,
        old_dtype: str,
        new_dtype: str,
        **params
    ) -> Set[int]:
        return {sheet_index}