import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    EventID: '',
    Status: '',
    Criterion: ''
}


export default function StatusTable() {
    const defaultMaterialTheme = createTheme();
    const [statusData, setStatusData] = useState([]);
    const StatusColumns = ["EventID", "Status", "Criterion"];
    const tableRef = useRef();


    const fetchMarketData = () => {
        fetch('/get_track_status').then(res => res.json()).then((data) => {
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setStatusData(data)
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
                columns={StatusColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={statusData.map((data) => {
                    return {
                        EventID: data[0],
                        Status: data[1],
                        Criterion: data[2]
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
  