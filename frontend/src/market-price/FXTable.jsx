import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    Currency: '',
    Rate: '',
}

export default function FXDataTable() {
    const defaultMaterialTheme = createTheme();
    const [FXData, setFXData] = useState([]);
    const FXColumns = ["Currency", "Rate"];
    const tableRef = useRef();

    const fetchMarketData = () => {
        fetch('/get_data/fx').then(res => res.json()).then((data) => {
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setFXData(data)
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
                columns={FXColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={FXData.map((data) => {
                    return {
                        Currency: data[0],
                        Rate: data[1],
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
  