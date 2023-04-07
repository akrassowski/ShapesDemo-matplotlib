DIR=gen2
mkdir -p $DIR
echo building in $DIR
/Applications/rti_connext_dds-7.0.0/bin/rtiddsgen -language Python -d $DIR -platform universal ShapeTypeExtended.idl 
