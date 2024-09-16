# Install
```bash
pip install -r requirements.txt
```

Rename .env_example to .env fill in the data in .env and you can run the program.

# Nats Jetstream
Turn on "jetstream" in nats
[Docker](https://github.com/nats-io/nats.docs/blob/master/running-a-nats-service/running/nats_docker/jetstream_docker.md?ysclid=m14rgaq6di872141023):
```bash
docker run -p 4222:4222 nats -js
```
[Kubernetes](https://docs.nats.io/running-a-nats-service/configuration/resource_management/configuration_mgmt/kubernetes_controller)

# Run
```bash
python bridge.py
```
Good luck using
 
