import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import DashboardIcon from '@mui/icons-material/Dashboard';
import LineAxisIcon from '@mui/icons-material/LineAxis';
// import LineStyleIcon from '@mui/icons-material/LineStyle';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BugReportIcon from '@mui/icons-material/BugReport';
// import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import Dashboard from './dashboard/Dashboard';
import MarketPrice from './market-price/MarketPrice';
import ExclusionTable from './logs/ExclusionTable';
import CustomReports from './custom-reports/CustomReports';


function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`home-tabpanel-${index}`}
      aria-labelledby={`home-tab-${index}`}
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

TabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
};

function a11yProps(index) {
  return {
    id: `home-tab-${index}`,
    'aria-controls': `home-tabpanel-${index}`,
  };
}

export default function Home() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange} aria-label="home tabs" centered>
          <Tab icon={<LineAxisIcon />} label="Market Price" {...a11yProps(0)} />
          <Tab icon={<DashboardIcon />} label="Dashboard" {...a11yProps(1)} />
          <Tab icon={<BugReportIcon />} label="Logs" {...a11yProps(2)} />
          <Tab icon={<AssessmentIcon />} label="Custom Reports" {...a11yProps(3)} />
        </Tabs>
      </Box>
      <TabPanel value={value} index={0}>
        <MarketPrice/>
      </TabPanel>
      <TabPanel value={value} index={1}>
        <Dashboard/>
      </TabPanel>
      <TabPanel value={value} index={2}>
        <ExclusionTable/>
      </TabPanel>
      <TabPanel value={value} index={3}>
        <CustomReports/>
      </TabPanel>
    </Box>
  );
}
