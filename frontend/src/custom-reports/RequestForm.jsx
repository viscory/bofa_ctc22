import React, { useState } from "react";
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import FormControl from '@mui/material/FormControl';
import Checkbox from '@mui/material/Checkbox';
import InputLabel from "@material-ui/core/InputLabel";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import MenuItem from "@material-ui/core/MenuItem";
import Select from "@material-ui/core/Select";

const defaultValues = {
  EventID: "",
  Measures: [],
  Categories: [],
  Aggregates: [],
};

const categories = [
  "Desk",
  "Trader",
  "Book",
  "BondID",
  "Currency"
];

const measures = [
  "Price",
  "NV",
  "Positions",
];

const aggregates = [
  "mean",
  "sum",
  "count",
  "std",
  "var",
  "min",
  "max"
];

const MenuProps = {
  getContentAnchorEl: null,
  anchorOrigin: {
    vertical: "bottom",
    horizontal: "center"
  },
  transformOrigin: {
    vertical: "top",
    horizontal: "center"
  },
  variant: "menu"
};


const RequestForm = () => {
  const [formValues, setFormValues] = useState(defaultValues);

  const isAllSelectedCategories =
    categories.length > 0 && formValues.Categories.length === categories.length;

  const isAllSelectedMeasures =
    measures.length > 0 && formValues.Measures.length === measures.length;

  const isAllSelectedAggregates =
    aggregates.length > 0 && formValues.Aggregates.length === aggregates.length;

  const handleChangeCategories = (event) => {
    const value = event.target.value;
    if (value[value.length - 1] === "all") {
      setFormValues({
        ...formValues,
        Categories: formValues.Categories.length === categories.length ? [] : categories,
      });
      return;
    }
    setFormValues({
      ...formValues,
      Categories: value,
    });
  };

  const handleChangeMeasures = (event) => {
    const value = event.target.value;
    if (value[value.length - 1] === "all") {
      setFormValues({
        ...formValues,
        Measures: formValues.Measures.length === measures.length ? [] : measures,
      });
      return;
    }
    setFormValues({
      ...formValues,
      Measures: value,
    });
  };

  const handleChangeAggregates = (event) => {
    const value = event.target.value;
    if (value[value.length - 1] === "all") {
      setFormValues({
        ...formValues,
        Aggregates: formValues.Aggregates.length === aggregates.length ? [] : aggregates,
      });
      return;
    }
    setFormValues({
      ...formValues,
      Aggregates: value,
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues({
      ...formValues,
      [name]: value,
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    fetch("/track",
    {
        method: "post",
        body: JSON.stringify(formValues),
        headers: {
          'Content-Type': 'application/json',
        },
    }).then(() => {
      setFormValues(defaultValues);
    })
  };

  return (
    <form onSubmit={handleSubmit}>
      <Grid container direction="column" sx={{ width: '40%', margin: 'auto' }}>
        <Grid item>
          <TextField
            required
            id="event-input"
            name="EventID"
            label="Event ID"
            type="text"
            variant="outlined"
            fullWidth
            value={formValues.EventID}
            onChange={handleInputChange}
          />
        </Grid>
        <Grid item sx={{ marginTop: 3, marginBottom: 3}}>
          <FormControl>
            <InputLabel>Categories</InputLabel>
            <Select
              multiple
              value={formValues.Categories}
              onChange={handleChangeCategories}
              renderValue={(selected) => selected.join(", ")}
              MenuProps={MenuProps}
              required
            >
              <MenuItem
                value="all"
              >
                <ListItemIcon>
                  <Checkbox
                    checked={isAllSelectedCategories}
                    indeterminate={
                      formValues.Categories.length > 0 && formValues.Categories.length < categories.length
                    }
                  />
                </ListItemIcon>
                <ListItemText
                  primary="Select All"
                />
              </MenuItem>
              {categories.map((option) => (
                <MenuItem key={option} value={option}>
                  <ListItemIcon>
                    <Checkbox checked={formValues.Categories.indexOf(option) > -1} />
                  </ListItemIcon>
                  <ListItemText primary={option} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item sx={{ marginTop: 3, marginBottom: 3}}>
          <FormControl>
            <InputLabel>Measures</InputLabel>
            <Select
              multiple
              value={formValues.Measures}
              onChange={handleChangeMeasures}
              renderValue={(selected) => selected.join(", ")}
              MenuProps={MenuProps}
              required
            >
              <MenuItem
                value="all"
              >
                <ListItemIcon>
                  <Checkbox
                    checked={isAllSelectedMeasures}
                    indeterminate={
                      formValues.Measures.length > 0 && formValues.Measures.length < measures.length
                    }
                  />
                </ListItemIcon>
                <ListItemText
                  primary="Select All"
                />
              </MenuItem>
              {measures.map((option) => (
                <MenuItem key={option} value={option}>
                  <ListItemIcon>
                    <Checkbox checked={formValues.Measures.indexOf(option) > -1} />
                  </ListItemIcon>
                  <ListItemText primary={option} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item sx={{ marginTop: 3, marginBottom: 3}}>
          <FormControl>
            <InputLabel>Aggregates</InputLabel>
            <Select
              multiple
              value={formValues.Aggregates}
              onChange={handleChangeAggregates}
              renderValue={(selected) => selected.join(", ")}
              MenuProps={MenuProps}
              required
            >
              <MenuItem
                value="all"
              >
                <ListItemIcon>
                  <Checkbox
                    checked={isAllSelectedAggregates}
                    indeterminate={
                      formValues.Aggregates.length > 0 && formValues.Aggregates.length < aggregates.length
                    }
                  />
                </ListItemIcon>
                <ListItemText
                  primary="Select All"
                />
              </MenuItem>
              {aggregates.map((option) => (
                <MenuItem key={option} value={option}>
                  <ListItemIcon>
                    <Checkbox checked={formValues.Aggregates.indexOf(option) > -1} />
                  </ListItemIcon>
                  <ListItemText primary={option} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Button variant="contained" color="primary" type="submit">
          Generate Report
        </Button>
      </Grid>
    </form>
  );
};
export default RequestForm;