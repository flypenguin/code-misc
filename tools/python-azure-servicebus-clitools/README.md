# Azure ServiceBus Clients

**WARNING: THOSE MAY BE OUTDATED AND DEFUNCT!**

Two python tools for ...

- sending messages to an Azure message bus
- receiving messages from an Azure message bus


## TL;DR

**This works only with topics, not with queues.** Also, of course, the topics/subscriptions must exist beforehand.

```bash
export AZURE_SB_TOPIC_SUBSCRIPTION="blablabla"
export AZURE_SB_TOPIC="blablabla"
export AZURE_SB_CONNECTION_STRING="blablabla"

# listen to a topic subscription
./recv-msg.py -l

# send a message to a topic (in parallel, in a different shell window)
./send-msg.py -t "hi ho"
```

The running `recv-msg.py` should pick this up. You have now sent a message to a topic, and received it via a topic subscription.
