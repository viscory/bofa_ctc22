import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    Desk: '',
    Currency: '',
    Positions: '',
    NV: ''
}

export default function CurrencyTable() {
    const defaultMaterialTheme = createTheme();
    const [currencyData, setCurrencyData] = useState([]);
    const [currencyColumns, setCurrencyColumns] = useState([]);
    const tableRef = useRef();


    const fetchCurrencyData = () => {
        fetch('/get_report/currency').then(res => res.json()).then((data) => {
            setCurrencyColumns(data[0]);
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setCurrencyData(data.slice(1,))
        });
    }

    useEffect(() => {
        fetchCurrencyData();
    }, [])
    
    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchCurrencyData();
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
                columns={currencyColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={currencyData.map((data) => {
                    let row = {};
                    for(let i = 0; i< currencyColumns.length; i++){
                        row[currencyColumns[i]] = data[i];
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
  