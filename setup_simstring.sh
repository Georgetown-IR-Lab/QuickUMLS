#!/usr/bin/env bash

# Checks if python version has been provided
if [[ -z "$1" ]]
then
    echo "No Python version specified." 1>&2;
    exit 1
fi

# read the release version (if provided)
if [[ ! -z "$2" ]]
then
    RELEASE_VERSION="$2"
else
    RELEASE_VERSION="1.1.4"
fi
RELEASE_FILENAME="${RELEASE_VERSION}.tar.gz"

RELEASE_URL="https://github.com/Georgetown-IR-Lab/simstring/archive/${RELEASE_FILENAME}"
echo $RELEASE_URL

# check if url returns 400 or 500 status
RELEASE_HTTP_CODE=`curl -o /dev/null --silent --head --write-out '%{http_code}' $RELEASE_URL`
if [[ "$RELEASE_HTTP_CODE" -ge "400" ]]
    then
    echo "Release not found" 1>&2;
    exit 1
fi

# If the version has been provided, it checks wether is version 2 or 3
if [[ "$1" != "2" && "$1" != "3" ]]
    then
    echo "Please specify a valid Python version (2 or 3)." 1>&2;
    exit 1
fi

# Set the python version here
PYTHON_VERSION=$1

# Remove any existsing simstring folder (ask for for permession!)
if [[ -d "simstring" ]]
then
    read -p "'simstring' directory exists. If you proceed, the folder will be deleted. Continue? [y/n] " yn
     case $yn in
        [Yy]* ) rm -rf simstring;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
fi

echo "Getting Simstring $RELEASE_VERSION..."
curl -O -L $RELEASE_URL

echo "Unpacking Simstring..."
tar -xf $RELEASE_FILENAME

rm -rf $RELEASE_FILENAME
RELEASE_FOLDER="simstring-${RELEASE_VERSION}"

echo "Making Simstring..."
cd "${RELEASE_FOLDER}"
if [[ "$PYTHON_VERSION" == "2" ]]
then
    python setup.py build_ext --inplace
else
    python3 setup.py build_ext --inplace
fi

# install in the right location
echo "Installing..."
cd ..
mkdir 'simstring'
touch 'simstring/__init__.py'

PLATFORM="$(uname -s)"

if [[ $PLATFORM == *"CYGWIN"* || $PLATFORM == *"MINGW"* ]]; then
    # we are on a NT system, so building creates DLLs
    cp ${RELEASE_FOLDER}/_*.dll simstring/
else
    # *nix system, so bulding stuff createsd SOs 
    cp ${RELEASE_FOLDER}/_*.so simstring/
fi

cp ${RELEASE_FOLDER}/simstring.py simstring/simstring.py

# remove remaining files
rm -rf "${RELEASE_FOLDER}"

echo "Done!"
