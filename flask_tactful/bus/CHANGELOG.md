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