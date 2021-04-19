#!/bin/sh
# Increment the tutorial example numbers so a new example may be inserted.

if [ "$#" != 1 ]; then
	echo "usage: $0 start_number" 1>&2
	exit 1
fi

lo=$1
hi=$lo

while /bin/true; do
	if [ -f example_$((hi+1)).yaml ]; then
		hi=$((hi+1))
	else
		break
	fi
done

j=$hi
while /bin/true; do
	k=$((j+1))
	mv example_$j.yaml example_$k.yaml
	sed -i "s/example_$j/example_$k/" ../../docs/tutorial.md
	sed -i "s/\"$j\"/\"$k\"/" ../../docs/tutorial.md
	if [ "$j" = "$lo" ]; then
		break
	fi
	j=$((j-1))
done
