valgrind --tool=massif --massif-out-file=$1 ./bin/main
massif-to-csv $1 $2

# --time-unit=ms
# --max-snapshots=20
