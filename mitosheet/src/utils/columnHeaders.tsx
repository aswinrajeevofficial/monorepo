import { ColumnHeader, ColumnID, ColumnIDsMap, DisplayColumnHeader, MultiIndexColumnHeader, PrimitiveColumnHeader } from "../types";


export const isPrimitiveColumnHeader = (columnHeader: ColumnHeader): columnHeader is PrimitiveColumnHeader => {
    return typeof columnHeader === 'string' || typeof columnHeader === 'number' || typeof columnHeader === 'boolean';
}

/**
 * Given a column header, returns a string that represents how to store this column
 * header on the front-end. 
 * 
 * NOTE: must match the equivalent function in mitosheet/column_headers.py
 * 
 * @param columnHeader The column header to display
 */
export const getDisplayColumnHeader = (columnHeader: ColumnHeader): DisplayColumnHeader => {
    if (isPrimitiveColumnHeader(columnHeader)) {
        return columnHeader.toString()
    } else {
        return columnHeader.map(c => c.toString()).filter(c => c !== '').join(', ')
    }
}

/**
 * 
 * @param columnIDsMap the column header map to turn into a map from column id to display headers
 * @returns a Record of ColumnID to display of a ColumnHeader
 */
export const columnIDMapToDisplayHeadersMap = (columnIDsMap: ColumnIDsMap): Record<ColumnID, DisplayColumnHeader> => {
    return Object.fromEntries(Object.entries(columnIDsMap).map(([columnID, columnHeader]) => {return [columnID, getDisplayColumnHeader(columnHeader)]}));
}

/**
 * When there is a dataframe with multi-index headers, there can also be column headers
 * that just are a single string (e.g. if you add a column using Mito). In this case, we
 * show this column header at the bottom of the column header levels, so this is easy to 
 * read, and so we have a utility for checking when this is the case.
 * 
 * @param columnHeader The column header to check
 */
const isSingleStringMultiIndexHeader = (columnHeader: ColumnHeader): boolean => {
    if (isPrimitiveColumnHeader(columnHeader)) {
        return true;
    }

    for (let i = 1; i < columnHeader.length; i++) {
        if (columnHeader[i] !== '') {
            return false
        } 
    }


    return true;
}

export const getColumnHeaderParts = (columnHeader: ColumnHeader): {lowerLevelColumnHeaders: MultiIndexColumnHeader, finalColumnHeader: PrimitiveColumnHeader} => {
    if (isPrimitiveColumnHeader(columnHeader)) {
        return {
            lowerLevelColumnHeaders: [],
            finalColumnHeader: columnHeader
        }
    } else {
        // First, we check if all elements in the column header except the first are empty strings
        // in which case we just set the single set element a the final column header, and the bunch
        // of empty strings as the lower level headers. This is just a visual trick to make things
        // look consistent and readable
        if (isSingleStringMultiIndexHeader(columnHeader)) {
            return {
                lowerLevelColumnHeaders: columnHeader.slice(1),
                finalColumnHeader: columnHeader[0]
            }
        }

        const lowerLevelColumnHeaders = columnHeader.slice(0, columnHeader.length - 1);
        const finalColumnHeader = columnHeader[columnHeader.length - 1];
        return {
            lowerLevelColumnHeaders: lowerLevelColumnHeaders,
            finalColumnHeader: finalColumnHeader
        }
    }
}

// Converts a row index into the level in the column header
export const rowIndexToColumnHeaderLevel = (columnHeader: MultiIndexColumnHeader, rowIndex: number): number => {
    if (isSingleStringMultiIndexHeader(columnHeader)) {
        return 0;
    }
    return columnHeader.length - (rowIndex * -1)
}

