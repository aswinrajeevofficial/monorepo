#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Saga Inc.
# Distributed under the terms of the GPL License.
from copy import copy
from typing import Any, Dict, List, Optional, Set, Tuple
from mitosheet.code_chunks.code_chunk import CodeChunk
from mitosheet.code_chunks.empty_code_chunk import EmptyCodeChunk

from mitosheet.state import State
from mitosheet.step_performers.step_performer import StepPerformer
from mitosheet.types import GraphID


class GraphDeleteStepPerformer(StepPerformer):
    """
    Deletes a graph from everywhere in the step.
    """

    @classmethod
    def step_version(cls) -> int:
        return 1

    @classmethod
    def step_type(cls) -> str:
        return 'graph_delete'

    @classmethod
    def saturate(cls, prev_state: State, params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    @classmethod
    def execute( # type: ignore
        cls,
        prev_state: State,
        graph_id: GraphID,
        **params
    ) -> Tuple[State, Optional[Dict[str, Any]]]:

        # Create a new step and save the parameters
        post_state = prev_state.copy()

        # Execute the graph delete
        del post_state.graph_data_dict[graph_id]

        return post_state, {
            'pandas_processing_time': 0 # No time spent on pandas, only metadata changes
        }

    @classmethod
    def transpile(
        cls,
        prev_state: State,
        post_state: State,
        params: Dict[str, Any],
        execution_data: Optional[Dict[str, Any]],
    ) -> List[CodeChunk]:

        # Graph steps don't add any generated code to the analysis script. 
        return [
            EmptyCodeChunk(
                prev_state, 
                post_state, 
                {
                    'display_name': 'Deleted graph',
                    'description_comment': 'Deleted a graph',
                }, 
                execution_data
            )
        ]
    
    @classmethod
    def get_modified_dataframe_indexes( # type: ignore
        cls, 
        graph_id: GraphID,
        **params
    ) -> Set[int]:
        return {-1}
