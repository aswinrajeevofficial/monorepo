// Copyright (c) Saga Inc.

import React, { useEffect } from 'react';
import MitoAPI, { getRandomId } from '../../jupyter/api';
import { GraphDataDict, GraphID, SheetData, UIState } from '../../types';
import Dropdown from '../elements/Dropdown';
import DropdownItem from '../elements/DropdownItem';
import { ModalEnum } from '../modals/modals';
import { getDefaultGraphParams } from '../taskpanes/Graph/graphUtils';

/*
    Helper function for finding all of the graph tab names
    that are created from a given sheet index
*/
export const getGraphTabNamesAndIDsFromSheetIndex = (sheetIndex: number, graphDataDict: GraphDataDict): ({graphTabName: string, graphID: GraphID})[] => {
    // Filter to only grapsh with the sheetIndex, and then get a list of the graph tab names
    const filteredGraphDataJSON: GraphDataDict = Object.fromEntries(Object.entries(graphDataDict || {}).filter(([, graphData]) => {
        return graphData.graphParams.graphCreation.sheet_index === sheetIndex
    }))

    return Object.entries(filteredGraphDataJSON).map(([graphID, graphData]) => {
        return {graphTabName: graphData.graphTabName, graphID: graphID}
    })
} 

/*
    Displays a set of actions one can perform on a data sheet tab, including
    deleting, duplicating, or renaming, and creating a sheet.
*/
export default function SheetTabActions(props: {
    setDisplayActions: React.Dispatch<React.SetStateAction<boolean>>,
    setIsRename: React.Dispatch<React.SetStateAction<boolean>>;
    setUIState: React.Dispatch<React.SetStateAction<UIState>>;
    closeOpenEditingPopups: () => void;
    mitoAPI: MitoAPI
    sheetIndex: number
    graphDataDict: GraphDataDict
    sheetDataArray: SheetData[]
}): JSX.Element {

    // Log opening the data sheet tab actions
    useEffect(() => {
        void props.mitoAPI.log(
            'clicked_data_sheet_tab_actions',
            {
                sheet_index: props.sheetIndex
            }
        )
    }, [])

    const onDelete = async (): Promise<void> => {
        const dependantGraphTabNamesAndIDs = getGraphTabNamesAndIDsFromSheetIndex(props.sheetIndex, props.graphDataDict)
        
        if (dependantGraphTabNamesAndIDs.length > 0) {
            props.setUIState(prevUIState => {
                return {
                    ...prevUIState,
                    currOpenModal: {
                        type: ModalEnum.DeleteGraphs, 
                        dependantGraphTabNamesAndIDs: dependantGraphTabNamesAndIDs,
                        sheetIndex: props.sheetIndex
                    }
                }
            })
        } else {
            // Select the previous sheet
            props.setUIState(prevUIState => {
                return {
                    ...prevUIState,
                    selectedTabType: 'data',
                    selectedSheetIndex: prevUIState.selectedSheetIndex > 0 ? prevUIState.selectedSheetIndex - 1 : 0,
                }
            })

            // Close 
            props.closeOpenEditingPopups();

            await props.mitoAPI.editDataframeDelete(props.sheetIndex)
        }


        
    }

    const onDuplicate = async (): Promise<void> => {
        // Close 
        props.closeOpenEditingPopups();
        
        await props.mitoAPI.editDataframeDuplicate(props.sheetIndex)
        
    }

    /* Rename helper, which requires changes to the sheet tab itself */
    const onRename = (): void => {
        props.setIsRename(true);
    }
    
    const graphData = async (): Promise<void> => {

        const newGraphID = getRandomId() // Create a new graph
        const graphParams = getDefaultGraphParams(props.sheetDataArray, props.sheetIndex)

        await props.mitoAPI.editGraph(
            newGraphID,
            graphParams,
            '100%',
            '100%',
            undefined, 
        );
    }

    return (
        <Dropdown
            closeDropdown={() => props.setDisplayActions(false)}
            width='small'
        >
            <DropdownItem
                title='Create graph'
                onClick={(e) => {
                    // Stop propogation so that the onClick of the sheet tab div
                    // doesn't compete updating the uiState to this sheet instead of
                    // the new graphID that we're creating
                    e?.stopPropagation()
                    void graphData()
                }}
            />
            <DropdownItem 
                title='Delete'
                onClick={(e) => {
                    // Stop propogation so that the onClick of the sheet tab div
                    // doesn't compete updating the uiState to the graphID that is gettind deleted
                    e?.stopPropagation()
                    void onDelete()
                }}
            />
            <DropdownItem 
                title='Duplicate'
                onClick={onDuplicate}
            />
            <DropdownItem 
                title='Rename'
                onClick={onRename}
            />
        </Dropdown>
    )
}

