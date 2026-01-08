import {useMemo} from 'react';

export const useParsedList = (rawString) => {
    return useMemo(() => {
        if (!rawString) return [];
        const separator = rawString.includes('\n') ? '\n' : '.';

        return rawString
            .split(separator)
            .map(text => text.trim())
            .filter(text => text.length > 0);

    }, [rawString]);
};

export const useFacilities = (rawString) => {
    return useMemo(()=>{
        if (!rawString) return [];
        return rawString.split(',').map(t => t.trim()).filter(t => t.length > 0);
    }, [rawString]);
};