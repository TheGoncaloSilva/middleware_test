# Clean up publisher
docker stop publisher
docker rm publisher

# Clean up IPC shared container
docker stop ipc_share_container
docker rm ipc_share_container

# Clean up subscriber
docker stop subscriber
docker rm subscriber