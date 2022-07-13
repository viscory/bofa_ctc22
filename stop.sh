if [ -f "pidfile" ]
then
	(cat "pidfile" | xargs kill) && rm "pidfile"
	./reset.sh
else
	echo "No pidfile, FICC-BACKEND not started"
fi
