class Logger():

    def __init__(self, path_to_log_file) -> None:
        self.path_to_log_file = path_to_log_file

    def get_config(self):
        logger_config = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(asctime)s\t%(levelname)s\t%(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",

                },
            },
            "handlers": {
                'default': {
                    'formatter': 'default',
                    'class': 'logging.StreamHandler',
                },
                'file_handler': {
                    'formatter': 'default',
                    'class': 'logging.FileHandler',
                    'filename': self.path_to_log_file,
                    'mode': 'a',
                },
                'rotating_file_handler': {
                    'formatter': 'default',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': self.path_to_log_file,
                    'mode': 'a',
                    'maxBytes': 10000000,
                    'backupCount': 100,
                },
                'time_rotating_file_handler': {
                    'formatter': 'default',
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': self.path_to_log_file,
                    'when': 'midnight',
                    'interval': 1
                },
            },
            "root": {
                "handlers": ["default", "time_rotating_file_handler"],
                "level": "DEBUG",
                "propagate": True,
            }
        }
        return logger_config
