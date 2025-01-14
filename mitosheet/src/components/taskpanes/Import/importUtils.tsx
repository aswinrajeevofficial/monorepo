import { fuzzyMatch } from "../../../utils/strings";
import { FileElement, ImportTaskpaneState } from "./ImportTaskpane";



/* 
    Helper function that gets an ending of a file, or
    undefined if no such file ending exists
*/
export const getFileEnding = (elementName: string): string | undefined => {
    try {
        // Take just the file ending
        const nameSplit = elementName.split('.');
        return nameSplit[nameSplit.length - 1];
    } catch {
        return undefined;
    }
}


/* 
    Helper function that, for a given file, returns if there is an 
    error in importing the file. 

    Helpful in displaying in-place errors that tells users they cannot
    import xlsx files.
*/
export const getInvalidFileError = (selectedElement: FileElement, excelImportEnabled: boolean): string | undefined => {
    // We do not display an error on directories, as you cannot
    // import them but we don't want to overload you
    if (selectedElement.isDirectory) {
        return undefined;
    }
    
    const VALID_FILE_ENDINGS = [
        'csv',
        'tsv',
        'txt',
        'tab',
    ]

    // If excel import is enabled, then add it as a valid ending
    if (excelImportEnabled) {
        VALID_FILE_ENDINGS.push('xlsx');
    }

    // Check if the file ending is a type that we support out of the box
    for (const ending of VALID_FILE_ENDINGS) {
        if (selectedElement.name.toLowerCase().endsWith(ending)) {
            return undefined;
        }
    }

    // We try and get the ending from the file
    const fileEnding = getFileEnding(selectedElement.name);
    if (fileEnding === undefined) {
        return 'Sorry, we don\'t support that file type.'
    } else if (fileEnding == 'xlsx') {
        return 'Upgrade to pandas>=0.25.0 and Python>3.6 to import Excel files.'
    } else {
        return `Sorry, we don't support ${fileEnding} files.`
    }
}

/* 
    Helper function that returns if the import button is usable, 
    and also the message to display on the button based on which
    element is selected.
*/
export const getImportButtonStatus = (selectedElement: FileElement | undefined, excelImportEnabled: boolean, loadingImport: boolean): {disabled: boolean, buttonText: string} => {
    if (selectedElement === undefined) {
        return {
            disabled: true,
            buttonText: 'Select a File to Import'
        };
    }
    if (selectedElement.isDirectory) {
        return {
            disabled: true,
            buttonText: 'That\'s a Directory. Select a File'
        };
    }
    const invalidFileError = getInvalidFileError(selectedElement, excelImportEnabled);
    if (invalidFileError !== undefined) {
        return {
            disabled: true,
            buttonText: 'Select a Supported File Type'
        };
    }

    if (loadingImport) {
        return {
            disabled: false,
            buttonText: 'Importing...'
        };
    }
    return {
        disabled: false,
        buttonText: 'Import ' + selectedElement.name
    };
}


export const getXLSXImportButtonText = (stepID: string | undefined, numSelectedSheets: number, loadingImport: boolean): string => {
    if (loadingImport) {
        return "Importing..."
    }
    return stepID === undefined 
        ? `Import ${numSelectedSheets} Selected Sheet${numSelectedSheets === 1 ? '' : 's'}` 
        : `Reimport ${numSelectedSheets} Selected Sheet${numSelectedSheets === 1 ? '' : 's'}`
}

export const getElementsToDisplay = (importState: ImportTaskpaneState): FileElement[] => {
    return importState.pathContents.elements?.filter(element => {
        return fuzzyMatch(element.name, importState.searchString) > .8;
    }).sort((elementOne, elementTwo) => {
        if (importState.sort === 'name_ascending') {
            return elementOne.name < elementTwo.name ? -1 : 1;
        } else if (importState.sort === 'name_descending') {
            return elementOne.name >= elementTwo.name ? -1 : 1;
        } else if (importState.sort === 'last_modified_ascending') {
            return elementOne.lastModified < elementTwo.lastModified ? -1 : 1;
        } else {
            return elementOne.lastModified >= elementTwo.lastModified ? -1 : 1;
        }
    })
}