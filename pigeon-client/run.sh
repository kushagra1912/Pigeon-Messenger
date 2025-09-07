docker build -t pigeon-client .

# for testing
# docker run --name pigeon-client --network my_network -ti --rm -p 6400:6400 pigeon-client

# docker run -ti --rm -p 6400:6400 pigeon-client
docker run -ti -p 6400:6400 pigeon-client
