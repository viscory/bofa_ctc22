import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TableRestaurantIcon from '@mui/icons-material/TableRestaurant';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import FeedIcon from '@mui/icons-material/Feed';
import LocalAtmIcon from '@mui/icons-material/LocalAtm';

import DeskTable from './DeskTable';
import BookTable from './BookTable';
import TraderTable from './TraderTable';
import CurrencyTable from './CurrencyTable';

function DashboardTabPanel(props) {
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

DashboardTabPanel.propTypes = {
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

export default function Dashboard() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange} aria-label="dashboard tabs">
          <Tab icon={<TableRestaurantIcon />} iconPosition="start" label="Desk" {...a11yProps(0)} />
          <Tab icon={<SupportAgentIcon />} iconPosition="start" label="Trader" {...a11yProps(1)} />
          <Tab icon={<FeedIcon />} iconPosition="start" label="Book" {...a11yProps(2)} />
          <Tab icon={<LocalAtmIcon />} iconPosition="start" label="Currency" {...a11yProps(3)} />

        </Tabs>
      </Box>
      <DashboardTabPanel value={value} index={0}>
        <DeskTable/>
      </DashboardTabPanel>
      <DashboardTabPanel value={value} index={1}>
        <TraderTable/>
      </DashboardTabPanel>
      <DashboardTabPanel value={value} index={2}>
        <BookTable/>
      </DashboardTabPanel>
      <DashboardTabPanel value={value} index={3}>
        <CurrencyTable/>
      </DashboardTabPanel>
    </Box>
  );
}
