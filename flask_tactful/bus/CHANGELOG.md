# Change Log

All notable changes to the bus will be documented in this file.
The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [< tag >] - < date >

### Added

### Changed

### Fixed

### Removed

### Deprecated

--- 

## [4.3.1] - 2024-03-21

### Added

- The bus can handle connection errors and will try to reconnect to the Redis server. Use `busReconnectionTimeout` to set the time in seconds to wait before trying to reconnect to the Redis server. The default value is 2 minutes.

Example:
```python
bus = TactfulRedisStreamBus(
        app=Flask(__name__),
        bus_url=TEST_REDIS_DB,
        group_name="tests",
        consumer_name="client1",
        max_stream_len=2,
        busReconnectionTimeout=120, # 2 minutes
        approximate_trimming=False # To get exact length trimming. Check: https://stackoverflow.com/a/67526831/14043328
    )
```


## [3.2.0] - 2024-02-07
   
### Added

- Now, you can add a `max_stream_len` to the `event` object instead of having a shared one accross all topics. This way, we can have a different `max_stream_len` for each topic i.e. stream.

Example:
```python

# Create your event 
event = Event(
  version= 2
  topic= "tactful.svc", 
  event= "TestEvent", 
  msg_id= '1234567890',
  max_stream_len= 100, # means the stream will only keep the last 100 messages
  profile_id= 1
)

```
--- 

[4.2.1] - 2024-03-03

### Fixed

- Trying to fix the lagging that happens when the bus starts and there are no subscribed topics. The solution is to not create the thread unless there are subscribed topics.

---