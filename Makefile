export MY_DIR=rest_server

test_1:
	python -m unittest rest_test
test_2:
	python -m unittest fs_test
test_3:
	python -m unittest httpd_test

test: test_1 test_2 test_3

run:
	ps -auxwwww | grep 'python ./httpd.py' | grep -v 'grep' | awk '{print $$2}' |  \
		xargs kill -9 || exit 0
	# ps -auxwwww | grep 'make run' | grep -v 'grep' | awk '{print $$2}' |  \
	#		xargs kill -9 || exit 0
	fg || exit 0
	python ./httpd.py

backup:
	cd .. ;  \
	~/sh/backup_to_temp.sh ${MY_DIR} ; \
	scp $(~/sh/backup_to_temp.sh "${MY_DIR}" | tee /dev/stderr |  \
		grep DONE | awk '{print $2}' ) yjlou@ec2.no-ip.org:/home/yjlou/temp_backups/ ;\
	cd -
