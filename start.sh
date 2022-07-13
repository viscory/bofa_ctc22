if [ ! -f "pidfile" ]
then
	python3 "`pwd`/src/event_generator.py" &
	echo $! >> "pidfile"
	python3 "`pwd`/src/market_data_producer.py" &
	echo $! >> "pidfile"
	python3 "`pwd`/src/trade_data_producer.py" &
	echo $! >> "pidfile"
	python3 "`pwd`/src/cash_adjuster.py" &
	echo $! >> "pidfile"
	python3 "`pwd`/src/portfolio_engine.py" &
	echo $! >> "pidfile"
else
	while true; do
		read -p "Running FICC-backend detected. Restart? (y/n) " yn
		case $yn in
			[Yy]* ) ./stop.sh && ./start.sh; break;;
			[Nn]* ) exit;;
			* ) echo "Please answer yes or no.";;
		esac
	done
fi
