import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    EventID: '',
    Desk: '',
    Trader: '',
    Book: '',
    BondID: '',
    Signal: '',
    Quantity: '',
    Price: '',
    Reason: ''
}

export default function FXDataTable() {
    const defaultMaterialTheme = createTheme();
    const [exclusionData, setExclusionData] = useState([]);
    const exclusionColumns = ["EventID", "Desk", "Trader", "Book", "BondID", "Signal", "Quantity", "Price", "Reason"];
    const tableRef = useRef();

    const fetchExclusionData = () => {
        fetch('/get_exclusions').then(res => res.json()).then((data) => {
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setExclusionData(data)
        });
    }

    useEffect(() => {
        fetchExclusionData();
    }, [])
    
    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchExclusionData();
        }, 1000)
        return () => clearInterval(intervalId);
    }, [])

    return (
    <div style={{ width: '100%', height: '100%' }}>
        <link
            rel="stylesheet"
            href="https://fonts.googleapis.com/icon?family=Material+Icons"
        />
        <ThemeProvider theme={defaultMaterialTheme}>
            <MaterialTable
                tableRef={tableRef}
                title=""
                columns={exclusionColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={exclusionData.map((data) => {
                    let row = {};
                    for(let i = 0; i< exclusionColumns.length; i++){
                        row[exclusionColumns[i]] = data[i];
                    }
                    return row;
                })}        
                options={{
                    filtering: true,
                    pageSize: 20,
                    pageSizeOptions:[20, 50, 100, 200],
                }}
            />
        </ThemeProvider>
    </div>

    )
  }
  