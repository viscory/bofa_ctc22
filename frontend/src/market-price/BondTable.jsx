import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    Bond: '',
    Currency: '',
    Value: ''
}

export default function BondDataTable() {
    const defaultMaterialTheme = createTheme();
    const [bondData, setBondData] = useState([]);
    const bondColumns = ["Bond", "Currency", "Value"];
    const tableRef = useRef();

    const fetchMarketData = () => {
        fetch('/get_data/bonds').then(res => res.json()).then((data) => {
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setBondData(data)
        });
    }
    
    useEffect(() => {
        fetchMarketData();
    }, [])
    
    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchMarketData();
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
                columns={bondColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={bondData.map((data) => {
                    return {
                        Bond: data[0],
                        Currency: data[1],
                        Value: data[2],
                    }
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
  