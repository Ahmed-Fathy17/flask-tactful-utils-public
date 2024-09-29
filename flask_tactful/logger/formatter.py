import logging
import traceback
import re
import time


class CustomFormatter(logging.Formatter):

    converter = time.gmtime
    isLocal = False
    
    def configure(self, config: dict):
        stage = config.get('STAGE', 'Local').lower()
        self.isLocal = (stage == 'local' or stage == 'development')
        
    def formatException(self, exc_info) -> str :
        if exc_info is None:
            return ''
        return f" execption={''.join(traceback.format_exception(*exc_info))}"
        
    def format(self, record):
        # Construct log message similar to Nodejs format
        timestamp = self.formatTime(record, "%a, %d %b %Y %H:%M:%S GMT")
        level = record.levelname.lower()
        message = record.getMessage()
        fields_to_log = ['pathname', 'funcName', 'lineno']
        args = ' '.join(f"{key}={value}" for key, value in record.__dict__.items() if key in fields_to_log )
        if record.exc_info is not None:
            args = args + self.formatException(record.exc_info)

        log_message = f"{timestamp} tactful.logger module={record.name} level={level} message=`{message} {args}`"

        if self.isLocal:
            return log_message
        else:
            return re.sub(r"\n", "_NEWLINE_", log_message)

