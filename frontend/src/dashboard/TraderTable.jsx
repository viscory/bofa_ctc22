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

export default function TraderTable() {
    const defaultMaterialTheme = createTheme();
    const [traderData, setTraderData] = useState([]);
    const [traderColumns, setTraderColumns] = useState([]);
    const tableRef = useRef();


    const fetchTraderData = () => {
        fetch('/get_report/bond').then(res => res.json()).then((data) => {
            setTraderColumns(data[0]);
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setTraderData(data.slice(1,))
        });
    }

    useEffect(() => {
        fetchTraderData();
    }, [])


    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchTraderData();
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
                columns={traderColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={traderData.map((data) => {
                    let row = {};
                    for(let i = 0; i< traderColumns.length; i++){
                        row[traderColumns[i]] = data[i];
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
  