import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    Desk: '',
    Trader: '',
    Book: '',
    BondID: '',
    Positions: '',
    NV: ''
}

export default function BookTable() {
    const defaultMaterialTheme = createTheme();
    const [bookData, setBookData] = useState([]);
    const [bookColumns, setBookColumns] = useState([]);
    const tableRef = useRef();


    const fetchBookData = () => {
        fetch('/get_report/position').then(res => res.json()).then((data) => {
            setBookColumns(data[0]);
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setBookData(data.slice(1,))
        });
    }

    useEffect(() => {
        fetchBookData();
    }, [])
    
    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchBookData();
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
                columns={bookColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={bookData.map((data) => {
                    let row = {};
                    for(let i = 0; i< bookColumns.length; i++){
                        row[bookColumns[i]] = data[i];
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
  