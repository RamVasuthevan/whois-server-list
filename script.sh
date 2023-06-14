#!/bin/bash

# Define the path to the Excel file in the git repository
filepath="whois-servers.xlsx"

# Define the directories to hold the file versions
olddir="old"
newdir="new"

# Create the directories
mkdir -p $olddir $newdir

# Checkout the 2nd last commit and copy the file to the old directory
git checkout HEAD~1
cp $filepath $olddir/old.xlsx

# Checkout the last commit and copy the file to the new directory
git checkout HEAD
cp $filepath $newdir/new.xlsx

# Extract the contents of the Excel files
unzip $olddir/old.xlsx -d $olddir
unzip $newdir/new.xlsx -d $newdir

# Compare the extracted contents and save to differences.txt
diff -r $olddir $newdir > ../differences.txt

# Print the location of the differences file
echo "The differences have been saved to $(pwd)/differences.txt"
