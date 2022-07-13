if [ -f "pidfile" ]
then
	(cat "pidfile" | xargs kill) && rm "pidfile"
	rm <(ls src/data | grep \.db$) -f
else
	echo "No pidfile, FICC-BACKEND not started"
fi
