
# FICC Coding Challenge - Code To Connect 2022

The challenge was to create a portfolio tracker. Please check the powerpoint deck to get a better idea of what I created. Ranked 2nd for the challenge.



## Run Locally

To deploy this project, you must setup the backend and frontend

For the frontend.
```bash
    cd frontend
    npm install --force
    npm start
```
The frontend does not use any environment variables, and there is nothing to configure

For the backend, first, please view the .env file in the root directory and make the necessary adjustments for your usescase. Used Python 3.10 for development
Then, please set up the environment using pipenv.
```bash
    pipenv install
    pipenv run
```

There are start, stop, reset scripts in the root directory. Namely, start.sh, stop.sh, reset.sh
Please only use start.sh when trying to start the backend. The PIDs of the spawned processes are stored in a pidfile, and stop.sh uses them to kill the relevant processes

Finally run this command to start the simulation. or simply send a get request at this endpoint
```bash
	curl 127.0.0.1:5001/start_simulation
```

This produces the generic files mentioned in the coding challenge
```curl -XPOST -H "Content-type: application/json" -d '{"Aggregates": "general", "Categories": "general", "Measures": "general", "EventID": 551}' '127.0.0.1:5001/track'```


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

### Default API host

`FLASK_HOST='127.0.0.1'`


### Port variables

`EVENT_GENERATOR_PORT = 5001`

`TRADE_DATA_PRODUCER_PORT = 5011`

`MARKET_DATA_PRODUCER_PORT=5021`

`PORTFOLIO_ENGINE_PORT=5121`

`CASH_ADJUSTER_PORT=5221`

`REPORT_GENERATOR_PORT=5002`

### Data Directories
`EVENTS_DIR=backend/data/events.json`

`INITIAL_DESK_DATA=backend/data/initial_cash.csv`

`INITIAL_BOND_DATA=backend/data/bond_details.csv`

`INITIAL_FX_DATA=backend/data/initial_fx.csv`

### Delay between events
`EVENT_PRODUCTION_DELAY=2500`

## Support

For support, don't.

