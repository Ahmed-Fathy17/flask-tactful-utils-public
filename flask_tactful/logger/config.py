import logging
import re

def configure_log_modules(LOG_MODULES: str):
    if LOG_MODULES is None:
        LOG_MODULES = ''
        
    enabled_modules = [module for module in re.split(r'[\s,]+', LOG_MODULES) if module]
    
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        is_enabled = any([re.match(module_regex, name) for module_regex in enabled_modules])
        logger.disabled = not is_enabled
        # or set the filter to always return false for those loggers
        # logger.addFilter(lambda record: False)
        
