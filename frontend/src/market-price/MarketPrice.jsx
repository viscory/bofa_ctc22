import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import FeedIcon from '@mui/icons-material/Feed';
import LocalAtmIcon from '@mui/icons-material/LocalAtm';
import BondDataTable from './BondTable';
import FXDataTable from './FXTable';

function MarketPriceTabPanel(props) {
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

MarketPriceTabPanel.propTypes = {
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
          <Tab icon={<FeedIcon />} iconPosition="start" label="Bonds" {...a11yProps(0)} />
          <Tab icon={<LocalAtmIcon />} iconPosition="start" label="FX" {...a11yProps(1)} />
        </Tabs>
      </Box>
      <MarketPriceTabPanel value={value} index={0}>
        <BondDataTable/>
      </MarketPriceTabPanel>
      <MarketPriceTabPanel value={value} index={1}>
        <FXDataTable/>
      </MarketPriceTabPanel>
    </Box>
  );
}
