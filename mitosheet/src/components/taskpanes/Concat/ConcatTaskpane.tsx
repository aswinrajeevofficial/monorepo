import React, { useState } from "react";
import MitoAPI from "../../../jupyter/api";
import useSyncedParams from "../../../hooks/useSyncedParams";
import { AnalysisData, ColumnHeader, ConcatParams, SheetData, StepType, UIState } from "../../../types"
import DropdownButton from "../../elements/DropdownButton";
import DropdownItem from "../../elements/DropdownItem";
import Select from "../../elements/Select";
import SelectAndXIconCard from "../../elements/SelectAndXIconCard";
import Toggle from "../../elements/Toggle";
import Tooltip from "../../elements/Tooltip";
import Col from "../../spacing/Col";
import Row from "../../spacing/Row";
import DefaultEmptyTaskpane from "../DefaultTaskpane/DefaultEmptyTaskpane";
import DefaultTaskpane from "../DefaultTaskpane/DefaultTaskpane";
import DefaultTaskpaneBody from "../DefaultTaskpane/DefaultTaskpaneBody";
import DefaultTaskpaneHeader from "../DefaultTaskpane/DefaultTaskpaneHeader";



interface ConcatTaskpaneProps {
    mitoAPI: MitoAPI;
    analysisData: AnalysisData;
    sheetDataArray: SheetData[];
    setUIState: React.Dispatch<React.SetStateAction<UIState>>;
}

/* 
    Given a list of column headers, returns a formatted string with the first num characters in the column headers
    and the number of column headers that didn't have any character in the first num characters of the list
*/
const getFirstCharactersOfColumnHeaders = (columnHeaders: ColumnHeader[], num: number): [string, number] => {
    const columnHeadersCopy = [...columnHeaders]
    let charsRemaining = num
    const columnHeadersToDisplay = []
    while (columnHeadersCopy.length > 0 && charsRemaining > 0) {
        const nextFullString = (columnHeadersCopy.shift() as string)
        let nextPartialString = ''
        for (let i = 0; i < nextFullString.length; i++) {
            if (charsRemaining > 0) {
                nextPartialString += nextFullString[i];
                charsRemaining--;
            }
        }
        columnHeadersToDisplay.push(nextPartialString)
    }
    return [columnHeadersToDisplay.join(', '), columnHeadersCopy.length]
}

/* 
    Constructs a message that says if all the column headers in a sheet are included in the concatanated sheet. 
    If any column headers are not included, it reports them to the user.
*/
const getColumnHeadersIncludedMessage = (notIncludedColumnsArray: ColumnHeader[][], arrIndex: number): JSX.Element => {
    if (notIncludedColumnsArray[arrIndex].length === 0) {
        return (<p>&#x2713; All columns are included in the concatenated sheet.</p>)
    } 
    const [columnHeadersString, numOtherColumnHeaders] = getFirstCharactersOfColumnHeaders(notIncludedColumnsArray[arrIndex], 25)
    
    if (numOtherColumnHeaders === 0) {
        return (<p>Columns <span className='text-color-gray-important'>{columnHeadersString}</span> are not included.</p>)
    } else {
        return (<p>Columns <span className='text-color-gray-important'>{columnHeadersString}</span> and <span className='text-color-gray-important'>{numOtherColumnHeaders}</span> others are not included.</p>)
    }
}

/* 
    This taskpane allows users to concatenate two or more 
    dataframes together.
*/
const ConcatTaskpane = (props: ConcatTaskpaneProps): JSX.Element => {

    const {params, setParams} = useSyncedParams<ConcatParams>(
        {
            join: 'inner',
            ignore_index: true,
            sheet_indexes: []
        },
        StepType.Concat, 
        props.mitoAPI,
        props.analysisData,
        50 // 50 ms debounce delay
    )

    // Make sure the user cannot select the newly created dataframe
    const [selectableSheetIndexes] = useState(props.sheetDataArray.map((sd, index) => index));

    // For each sheet concatonated together, find all of the columns that are not included in the final result
    const concatSheetColumnHeaders = Object.values(props.sheetDataArray[props.sheetDataArray.length - 1]?.columnIDsMap || {})
    const notIncludedColumnsArray = params?.sheet_indexes.map(sheetIndex => {
        return Object.values(props.sheetDataArray[sheetIndex]?.columnIDsMap || {}).filter(columnHeader => {
            // Because concat_edit makes a new sheet and you can't reopen the concat taskpane or reorder sheets,
            // the sheet this taskpane creates is always the last sheet in the sheetDataArray 
            return !concatSheetColumnHeaders.includes(columnHeader)
        })
    })
    
    if (params === undefined) {
        return (<DefaultEmptyTaskpane setUIState={props.setUIState} message="Import at least two datasets before concating."/>)
    }

    const dataframeCards: JSX.Element[] = params.sheet_indexes.map((sheetIndex, arrIndex) => {
        return (
            <div key={arrIndex}>
                <SelectAndXIconCard 
                    titleMap={Object.fromEntries(props.sheetDataArray.map((sheetData, index) => {
                        return [index + '', sheetData.dfName]
                    }))}
                    value={sheetIndex + ''}
                    onChange={(newSheetIndexStr) => {
                        const newSheetIndex = parseInt(newSheetIndexStr);
                        setParams(prevConcatParams => {
                            const newSheetIndexes = [...prevConcatParams.sheet_indexes];
                            newSheetIndexes[arrIndex] = newSheetIndex;

                            return {
                                ...prevConcatParams,
                                sheet_indexes: newSheetIndexes
                            }
                        })
                    }}
                    onDelete={() => {
                        setParams(prevConcatParams => {
                            const newSheetIndexes = [...prevConcatParams.sheet_indexes];
                            newSheetIndexes.splice(arrIndex, 1);

                            return {
                                ...prevConcatParams,
                                sheet_indexes: newSheetIndexes
                            }
                        })
                    }}
                    selectableValues={Object.keys(props.sheetDataArray)} // Note the cast to strings
                />
                {notIncludedColumnsArray !== undefined &&
                    <Row className='text-subtext-1'>
                        {getColumnHeadersIncludedMessage(notIncludedColumnsArray, arrIndex)}
                    </Row>
                }
            </div>
        )
    })

    return (
        <DefaultTaskpane>
            <DefaultTaskpaneHeader 
                header="Concatenate Sheet"
                setUIState={props.setUIState}            
            />
            <DefaultTaskpaneBody>
                <Row justify='space-between' align='center'>
                    <Col>
                        <p className='text-header-3'>
                            Join Type
                        </p>
                    </Col>
                    <Col>
                        <Select 
                            value={params.join}
                            onChange={(newJoin: string) => {
                                setParams(prevConcatParams => {
                                    return {
                                        ...prevConcatParams,
                                        join: newJoin as 'inner' | 'outer'
                                    }
                                })
                            }}
                            width='medium'
                        >
                            <DropdownItem
                                title='inner'
                                subtext="Only includes columns that exist in all sheets"
                            />
                            <DropdownItem
                                title="outer"
                                subtext="Includes all columns from all sheets, regardless of if these columns are in the other sheets."
                            />
                        </Select>
                    </Col>
                </Row>
                <Row justify='space-between' align='center'>
                    <Col>
                        <Row align='center' suppressTopBottomMargin>
                            <p className='text-header-3'>
                                Ignore Existing Indexes &nbsp;
                            </p>
                            <Tooltip title={"When on, the resulting dataframe will have indexes 0, 1, 2, etc.. This is useful if you're concatenating objects that don't have meaningful index information."}/>
                        </Row>
                        
                    </Col>
                    <Col>
                        <Toggle 
                            value={params.ignore_index}
                            onChange={() => {
                                setParams(prevConcatParams => {
                                    return {
                                        ...prevConcatParams,
                                        ignore_index: !prevConcatParams.ignore_index
                                    }
                                })
                            }}                      
                        />
                    </Col>
                </Row>
                <Row justify='space-between' align='center'>
                    <Col>
                        <p className='text-header-3'>
                            Dataframes to Concatenate
                        </p>
                    </Col>
                    <Col>
                        <DropdownButton
                            text='+ Add'
                            width='small'
                            searchable
                        >   
                            {/** We allow users to select all dataframes in the sheet, as some users want this */}
                            {[
                                <DropdownItem
                                    key={-1}
                                    title="Add all sheets"
                                    onClick={() => {
                                        setParams(prevConcatParams => {
                                            const newSheetIndexes = [...selectableSheetIndexes];
                    
                                            return {
                                                ...prevConcatParams,
                                                sheet_indexes: newSheetIndexes
                                            }
                                        })
                                    }}
                                />
                            ].concat(props.sheetDataArray.filter((sheetData, index) => {
                                if (!selectableSheetIndexes.includes(index)) {
                                    return false;
                                }
                                return true;
                            }).map((sheetData, index) => {
                                return (
                                    <DropdownItem
                                        key={index}
                                        title={sheetData.dfName}
                                        onClick={() => {
                                            setParams(prevConcatParams => {
                                                const newSheetIndexes = [...prevConcatParams.sheet_indexes];
                                                newSheetIndexes.push(index);
                        
                                                return {
                                                    ...prevConcatParams,
                                                    sheet_indexes: newSheetIndexes
                                                }
                                            })
                                        }}
                                    />
                                )
                            }))}
                        </DropdownButton>
                    </Col>
                </Row>
                {dataframeCards}
            </DefaultTaskpaneBody>

        </DefaultTaskpane>
    )
}

export default ConcatTaskpane;