#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Mito.
# Distributed under the terms of the Modified BSD License.

from copy import deepcopy
from collections import OrderedDict
from typing import List, Dict
import pandas as pd

from mitosheet.sheet_functions.types.utils import get_mito_type
from mitosheet.column_headers import ColumnIDMap

# Constants for where the dataframe in the state came from
DATAFRAME_SOURCE_PASSED = 'passed' # passed in mitosheet.sheet
DATAFRAME_SOURCE_IMPORTED = 'imported' # imported through a simple import
DATAFRAME_SOURCE_PIVOTED = 'pivoted' # created through a pivot
DATAFRAME_SOURCE_MERGED = 'merged' # created through a merge
DATAFRAME_SOURCE_DUPLICATED = 'duplicated' # created through a sheet duplication

# Constants used for formatting. Defined here to avoid circular imports
FORMAT_DEFAULT = 'default'
FORMAT_PLAIN_TEXT = 'plain text'
FORMAT_PERCENTAGE = 'percentage'
FORMAT_ACCOUNTING = 'accounting'
FORMAT_CURRENCY = 'currency'
FORMAT_ROUND_DECIMALS = 'round decimals'
FORMAT_K_M_B = 'k_m_b'
FORMAT_SCIENTIFIC_NOTATION = 'scientific notation'

class State():
    """
    State is a container that stores the current state of a Mito analysis,
    where each step that is applied takes a state as input and creates a
    new state as output. 

    It stores the obvious things, like the dataframes and their names, but 
    also other helper pieces of state like: the column formulas, the filters,
    etc.
    """

    def __init__(self, 
            dfs: List[pd.DataFrame], 
            df_names: List[str]=None,
            df_sources: List[str]=None,
            column_ids: ColumnIDMap=None,
            column_metatype=None,
            column_type=None,
            column_spreadsheet_code=None,
            column_python_code=None,
            column_evaluation_graph=None,
            column_filters=None,
            column_format_types: List[Dict[str, Dict[str, str]]]=None
        ):

        # The dataframes that are in the state
        self.dfs = dfs

        # The df_names are composed of two parts:
        # 1. The names of the variables passed into the mitosheet.sheet call (which don't change over time).
        # 2. The names of the dataframes that were created during the analysis (e.g. by a merge).
        # Until we get them from the frontend as an update_event, we default them to df1, df2, ...
        self.df_names = df_names if df_names is not None else [f'df{i + 1}' for i in range(len(dfs))] 

        # The df sources are where the actual dataframes come from, e.g.
        # how the dataframe was created. If not df sources passed, then this is in the
        # initialize state, and so these dataframes were passed to the mitosheet
        # call
        self.df_sources = df_sources if df_sources is not None else [DATAFRAME_SOURCE_PASSED for _ in dfs]

        # We then make a column id map if we do not already have one, so that we can identify each
        # of the columns from their static ids through the rest of the analysis. 
        # NOTE: every state variable below that is defined per column is access by _ids_ not
        # by column headers. The column headers _only_ index into the dataframe itself
        self.column_ids = column_ids if column_ids else ColumnIDMap(dfs)

        # The column_metatype is if it stores formulas or values
        self.column_metatype = column_metatype if column_metatype is not None else [
            {column_id: 'value' for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]

        # The column_type is the type of the series in this column 
        self.column_type = column_type if column_type is not None else [
            {
                column_id: get_mito_type(df[column_header]) 
                for column_id, column_header, in self.column_ids.get_column_ids_map(sheet_index).items()
            }
            for sheet_index, df in enumerate(dfs)
        ]

        # We make column_spreadsheet_code an ordered dictonary to preserve the order the formulas
        # are inserted, which in turn makes sure when we save + rerun an analysis, it's recreated
        # in the correct order (and thus the column order is preserved).
        self.column_spreadsheet_code = column_spreadsheet_code if column_spreadsheet_code is not None else [
            {column_id: '' for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]
        self.column_python_code = column_python_code if column_python_code is not None else [
            {column_id: '' for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]
        self.column_evaluation_graph = column_evaluation_graph if column_evaluation_graph is not None else [
            {column_id: set() for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]
        self.column_filters = column_filters if column_filters is not None else [
            {column_id: {'operator': 'And', 'filters': []} for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]

        self.column_format_types = column_format_types if column_format_types is not None else [
            {column_id: {'type': 'default'} for column_id in self.column_ids.get_column_ids(sheet_index)} 
            for sheet_index in range(len(dfs))
        ]
    
    def __copy__(self):
        """
        If you copy a state using the copy() function, this Python
        function is called, and returns a shallow copy of the state
        """
        return State(
            [df.copy(deep=False) for df in self.dfs],
            df_names=deepcopy(self.df_names),
            df_sources=deepcopy(self.df_sources),
            column_ids=deepcopy(self.column_ids),
            column_metatype=deepcopy(self.column_metatype),
            column_type=deepcopy(self.column_type),
            column_spreadsheet_code=deepcopy(self.column_spreadsheet_code),
            column_python_code=deepcopy(self.column_python_code),
            column_evaluation_graph=deepcopy(self.column_evaluation_graph),
            column_filters=deepcopy(self.column_filters),
            column_format_types=deepcopy(self.column_format_types)
        )


    def __deepcopy__(self, memo):
        """
        If you copy a state using the deepcopy() function, this Python
        function is called, and returns a deep copy of the state
        """
        return State(
            [df.copy(deep=True) for df in self.dfs],
            df_names=deepcopy(self.df_names),
            df_sources=deepcopy(self.df_sources),
            column_ids=deepcopy(self.column_ids),
            column_metatype=deepcopy(self.column_metatype),
            column_type=deepcopy(self.column_type),
            column_spreadsheet_code=deepcopy(self.column_spreadsheet_code),
            column_python_code=deepcopy(self.column_python_code),
            column_evaluation_graph=deepcopy(self.column_evaluation_graph),
            column_filters=deepcopy(self.column_filters),
            column_format_types=deepcopy(self.column_format_types)
        )

    def add_df_to_state(
            self, 
            new_df: pd.DataFrame, 
            df_source: str, 
            sheet_index=None,
            df_name=None,
            format_types=None,
            use_deprecated_id_algorithm: bool=False
        ):
        """
        Helper function for adding a new dataframe to this state,
        and keeping all the other variables in sync.

        If sheet_index is defined, then will replace the dataframe
        that is currently at the index. Otherwise, if sheet_index is
        not defined, then will append the df to the end of the state
        """
        if sheet_index is None:
            # Update dfs by appending new df
            self.dfs.append(new_df)
            # Also update the dataframe name
            if df_name is None:
                self.df_names.append(f'df{len(self.df_names) + 1}')
            else:
                self.df_names.append(df_name)

            # Save the source of this dataframe
            self.df_sources.append(df_source)

            # Add this to the column_ids map
            column_ids = self.column_ids.add_df(new_df, use_deprecated_id_algorithm=use_deprecated_id_algorithm)

            # Update all the variables that depend on column_headers
            self.column_metatype.append({column_id: 'value' for column_id in column_ids})
            self.column_type.append({column_id: get_mito_type(new_df[column_header]) for column_id, column_header in column_ids.items()})
            self.column_spreadsheet_code.append({column_id: '' for column_id in column_ids})
            self.column_python_code.append({column_id: '' for column_id in column_ids})
            self.column_evaluation_graph.append({column_id: set() for column_id in column_ids})
            self.column_filters.append({column_id: {'operator':'And', 'filters': []} for column_id in column_ids})
            self.column_format_types.append({column_id: {'type': FORMAT_DEFAULT} for column_id in column_ids} if format_types is None else format_types)

            # Return the index of this sheet
            return len(self.dfs) - 1
        else:

            # Update dfs by switching which df is at this index specifically
            self.dfs[sheet_index] = new_df
            # Also update the dataframe name, if it is passed. Otherwise, we don't change it
            if df_name is not None:
                self.df_names[sheet_index] = df_name

            # Save the source of this dataframe, if it is passed. Otherwise, don't change it
            if df_source is not None:
                self.df_sources[sheet_index] = df_source

            # Add this to the column_ids map
            column_ids = self.column_ids.add_df(new_df, sheet_index=sheet_index, use_deprecated_id_algorithm=use_deprecated_id_algorithm)

            # Update all the variables that depend on column_headers
            self.column_metatype[sheet_index] = {column_id: 'value' for column_id in column_ids}
            self.column_type[sheet_index] = {column_id: get_mito_type(new_df[column_header]) for column_id, column_header in column_ids.items()}
            self.column_spreadsheet_code[sheet_index] = {column_id: '' for column_id in column_ids}
            self.column_python_code[sheet_index] = {column_id: '' for column_id in column_ids}
            self.column_evaluation_graph[sheet_index] = {column_id: set() for column_id in column_ids}
            self.column_filters[sheet_index] = {column_id: {'operator':'And', 'filters': []} for column_id in column_ids}
            self.column_format_types[sheet_index] = {column_id: {'type': FORMAT_DEFAULT} for column_id in column_ids} if format_types is None else format_types

            # Return the index of this sheet
            return sheet_index
    
    def does_sheet_index_exist_within_state(self, sheet_index):
        """
        Returns true iff a sheet_index exists within this state
        """
        return not (sheet_index < 0 or sheet_index >= len(self.dfs))

    def move_to_deprecated_id_algorithm(self):
        """
        This helper function will move the entire state to the new IDs,
        for backwards compatibility reasons. Namely, users who pass
        dataframes to mito directly have a bulk_old_rename appended to 
        the start of their analysis that calls this function. 

        This moves the IDs to what they would have been if there was a 
        preprocessing step that had run, that had performed renames on
        the column headers before they were allowed into Mito. Brutal.
        """
        from mitosheet.step_performers.bulk_old_rename.deprecated_utils import make_valid_header

        # Loop over all the attributes of this object
        for key, value in self.__dict__.items():
            # And for anything defined on columns, update it to the new id schema
            if key.startswith('column') and key != 'column_ids':
                new_value = [
                    {
                        make_valid_header(k): v for k, v in column_map.items()
                    } 
                    for column_map in value
                ]
                self.__setattr__(key, new_value)
        
        # Then, update the column_evaluation_graph to use the old format as well
        new_column_evaluation_graph = [
            {
                column_id: {make_valid_header(cid) for cid in dependency_list}
                for column_id, dependency_list in column_evaluation_graph_map.items()
            }
            for column_evaluation_graph_map in self.column_evaluation_graph
        ]
        
        self.column_evaluation_graph = new_column_evaluation_graph
        
        # Then, update the column ids mapping object itself
        self.column_ids.move_to_deprecated_id_format()

    