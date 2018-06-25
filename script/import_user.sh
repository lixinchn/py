oldpwd=`pwd`
cd $oldpwd
for((i=0;i<=6;i++));
do
nohup /usr/local/bin/python ./import_user_to_future.py $i > /dev/null &
done