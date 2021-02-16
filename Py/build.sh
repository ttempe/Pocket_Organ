
rm *.mpy
for FILE in $(ls *.py)
do
	mpy-cross $FILE
done

