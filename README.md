# Mastodon usage - counting toots with Apache Pinot  

[Mastodon](https://joinmastodon.org/) is a _decentralized_ social networking platform. Mastodon users are members of a _specific_ Mastodon server, and servers are capable of joining other servers to form a global (or at least federated) social network.

I wanted to start exploring Mastodon usage, and perform some exploratory data analysis of user activity, server popularity and language usage. You may want to jump straight to the [data analysis](#data-analysis)

Tools used
- [Mastodon.py](https://mastodonpy.readthedocs.io/) - Python library for interacting with the Mastodon API
- [Apache Kafka](https://kafka.apache.org/) - distributed event streaming platform
- [Apache Pinot](https://dev.startree.ai/docs/pinot/recipes/) - Real-Time OLAP database
- [Streamlit](https://streamlit.io/) - Python web framework


![mastodon architecture](./docs/pinot_architecture.png)

# Data processing
We will us Kafka as distributed stream processing platform to collect data from multiple instances. To run Kafka and Apache Pinot, run the following:

```console
 docker-compose up -d
 ```

# Data collection

## Setup virtual python environment
Create a [virtual python](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) environment to keep dependencies separate. The _venv_ module is the preferred way to create and manage virtual environments. 

 ```console
python3 -m venv env
```

Before you can start installing or using packages in your virtual environment you’ll need to activate it.

```console
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
 ```


## Federated timeline
These are the most recent public posts from people on this and other servers of the decentralized network that this server knows about.

## Mastodon listener
The python `mastodonlisten` application listens for public posts to the specified server, and sends each toot to Kafka. You can run multiple Mastodon listeners, each listening to the activity of different servers

```console
python mastodonlisten.py --baseURL https://mastodon.social --enableKafka
```

These ones create a reasonable amount of messages:

```console

python mastodonlisten.py --baseURL https://fosstodon.org/ --public --enableKafka --quiet
python mastodonlisten.py --baseURL https://mstdn.social/ --public --enableKafka --quiet
python mastodonlisten.py --baseURL https://mastodon.cloud/ --public --enableKafka --quiet
python mastodonlisten.py --baseURL https://mas.to/ --public --enableKafka --quiet
python mastodonlisten.py --baseURL https://universeodon.com --public --enableKafka --quiet
python mastodonlisten.py --baseURL https://masto.ai/ --public --enableKafka --quiet
```

## Testing producer (optional)
As an optional step, you can check that AVRO messages are being written to kafka

```console
kafka-avro-console-consumer --bootstrap-server localhost:9092 --topic mastodon-topic --from-beginning
```

```console
kcat -C -b localhost:9092 -t mastodon-topic -s value=avro -r http://localhost:8081 -e
```

## Pinot

```bash
docker run \
   --network mastodon \
   -v $PWD/pinot:/config \
   apachepinot/pinot:0.12.0-arm64 AddTable \
     -schemaFile /config/schema.json \
     -tableConfigFile /config/table.json \
     -controllerHost "pinot-controller" \
    -exec
```

# Data analysis

To analyze the data, we're going to use Streamlit, which you can run with the following command:

```bash
streamlit run app.py
```

Once you've done that, navigate to http://localhost:8501
