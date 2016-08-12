# Script variables
RELEASE_VERSION="v1.1.1"
RELEASE_FILENAME="simstring_$RELEASE_VERSION.tar.gz"
RELEASE_URL="https://github.com/Georgetown-IR-Lab/simstring/releases/download/$RELEASE_VERSION/$RELEASE_FILENAME"

# Checks if python version has been provided
if [[ -z "$1" ]]
then
    echo "No Python version specified." 1>&2;
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
    read -p "'simstring' directory exists. If you proceed, the folder will be deleted. Continue? [y/n]" yn
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

echo "Making Simstring..."
cd "simstring"
if [[ "$PYTHON_VERSION" == "2" ]]
then
    bash "install_python.sh"
else
    bash "install_python3.sh"
fi

# install in the right location
echo "Installing..."
cd ..
cp -R "simstring/release" .
rm -rf "simstring"
mv "release" "simstring"
touch "simstring/__init__.py"
echo "Done!"
