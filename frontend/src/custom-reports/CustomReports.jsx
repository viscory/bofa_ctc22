import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import FlagSharpIcon from '@mui/icons-material/FlagSharp';
import HistoryIcon from '@mui/icons-material/History';
import StatusTable from './StatusTable';
import RequestForm from './RequestForm';

function CustomReportsTabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

CustomReportsTabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
};

function a11yProps(index) {
  return {
    id: `dashboard-tab-${index}`,
    'aria-controls': `dashboard-tabpanel-${index}`,
  };
}

export default function MarketPrice() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange} aria-label="dashboard tabs">
          <Tab icon={<FlagSharpIcon />} iconPosition="start" label="Request" {...a11yProps(0)} />
          <Tab icon={<HistoryIcon />} iconPosition="start" label="Status" {...a11yProps(1)} />
        </Tabs>
      </Box>
      <CustomReportsTabPanel value={value} index={0}>
        <RequestForm/>
      </CustomReportsTabPanel>
      <CustomReportsTabPanel value={value} index={1}>
        <StatusTable/>
      </CustomReportsTabPanel>
    </Box>
  );
}
