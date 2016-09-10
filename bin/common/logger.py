import logging
import logging.handlers

levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

formats = {
    "syslog":"%(levelname)s %(name)s[%(process)d]:%(asctime)s %(message)s",
    "default":"%(asctime)s %(levelname)s %(name)s[%(process)d]: %(message)s"
}

def _get_handler(handlertype, address):
    if handlertype == "file":
        address = address or "/var/log/gwss/gwss.log"
        return logging.handlers.TimedRotatingFileHandler(address, when="midnight", backupCount=7)
    elif handlertype == "syslog":
        # No address means localhost:514
        if address and len(address.split(":")) > 1:
            # We assume this is a distant syslog address if it has port separator
            address = address.split(":")
        return logging.handlers.SysLogHandler(arg)
    if address:
        return logging.StreamHandler(open(addresss))
    return logging.StreamHandler()


def get_logger_from_config(log_config_list, logname=None):
    # No filter for the whole logger. Each handler define its own
    logger = logging.getLogger(logname)
    logger.setLevel(logging.NOTSET)
    for log_config in log_config_list:
        logtype = log_config.get("type", "stream")
        # Default paths are handled by _get_handler. Each handler has its own default
        logpath = log_config.get("path", None)
        loglevel = log_config.get("level", "INFO")
        logformat = log_config.get("format", "default")

        handler = _get_handler(logtype, logpath)
        handler.setLevel(levels.get(loglevel, logging.INFO))
        log_format = logging.Formatter(formats.get(logformat,formats["default"]))
        handler.setFormatter(log_format)
        logger.addHandler(handler)
    return logger
