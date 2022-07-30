import MaterialTable from 'material-table';
import { ThemeProvider, createTheme } from '@mui/material';

import React, { useEffect, useState, useRef } from 'react';

const filters = {
    Desk: '',
    Cash: ''
}

export default function DeskTable() {
    const defaultMaterialTheme = createTheme();
    const [deskData, setDeskData] = useState([]);
    const [deskColumns, setDeskColumns] = useState([]);
    const tableRef = useRef();


    const fetchDeskData = () => {
        fetch('/get_report/cash').then(res => res.json()).then((data) => {
            setDeskColumns(data[0]);
            if(tableRef.current.state.columns){
                tableRef.current.state.columns.map((column) => {
                    filters[column.field] =  column.tableData.filterValue;
                });
            }
            setDeskData(data.slice(1,))
        });
    }

    useEffect(() => {
        fetchDeskData();
    }, [])

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchDeskData();
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
                columns={deskColumns.map((field) => {
                    return {
                        title: field,
                        field: field,
                        defaultFilter: filters[field]
                    }
                })}
                data={deskData.map((data) => {
                    let row = {};
                    for(let i = 0; i< deskColumns.length; i++){
                        row[deskColumns[i]] = data[i];
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
  