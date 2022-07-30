if [ -f "pidfile" ]
then
	./reset.sh
	(cat "pidfile" | xargs kill) && rm "pidfile"
else
	echo "No pidfile, FICC-BACKEND not started"
fi
