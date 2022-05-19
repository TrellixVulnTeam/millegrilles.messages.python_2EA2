import os

from millegrilles.messages import Constantes

from typing import Optional


CONST_OPTIONAL_PARAMS = [
    Constantes.ENV_MQ_CONNECTION_ATTEMPTS,
    Constantes.ENV_MQ_RETRY_DELAY,
    Constantes.ENV_MQ_HEARTBEAT,
    Constantes.ENV_MQ_BLOCKED_CONNECTION_TIMEOUT,
]


class ConfigurationPika:
    """
    Configuration de connexion avec Pika (pour RabbitMQ)
    """

    def __init__(self):
        self.hostname: Optional[str] = None
        self.port: Optional[int] = None
        self.ca_pem_path: Optional[str] = None
        self.cert_pem_path: Optional[str] = None
        self.key_pem_path: Optional[str] = None

        # Valeurs avec defaults
        self.connection_attempts = 2
        self.retry_delay = 10
        self.heartbeat = 30
        self.blocked_connection_timeout = 10

    def get_env(self) -> dict:
        """
        Extrait l'information pertinente pour pika de os.environ
        :return: Configuration dict
        """
        config = dict()
        config[Constantes.ENV_MQ_HOSTNAME] = os.environ.get(Constantes.ENV_MQ_HOSTNAME) or 'mq'
        config[Constantes.ENV_MQ_PORT] = os.environ.get(Constantes.ENV_MQ_PORT) or '5673'
        config[Constantes.ENV_CA_PEM] = os.environ.get(Constantes.ENV_CA_PEM)
        config[Constantes.ENV_CERT_PEM] = os.environ.get(Constantes.ENV_CERT_PEM)
        config[Constantes.ENV_KEY_PEM] = os.environ.get(Constantes.ENV_KEY_PEM)

        for opt_param in CONST_OPTIONAL_PARAMS:
            value = os.environ.get(opt_param)
            if value is not None:
                config[opt_param] = value

        return config

    def parse_config(self, configuration: dict):
        """
        Conserver l'information de configuration
        :param configuration:
        :return:
        """
        self.hostname = configuration.get(Constantes.ENV_MQ_HOSTNAME) or 'mq'
        self.port = int(configuration.get(Constantes.ENV_MQ_PORT) or '5673')
        self.ca_pem_path = configuration[Constantes.ENV_CA_PEM]
        self.cert_pem_path = configuration[Constantes.ENV_CERT_PEM]
        self.key_pem_path = configuration[Constantes.ENV_KEY_PEM]

        # Valeurs avec defaults
        self.connection_attempts = configuration.get(
            Constantes.ENV_MQ_CONNECTION_ATTEMPTS) or self.connection_attempts
        self.retry_delay = configuration.get(
            Constantes.ENV_MQ_RETRY_DELAY) or self.retry_delay
        self.heartbeat = configuration.get(
            Constantes.ENV_MQ_HEARTBEAT) or self.heartbeat
        self.blocked_connection_timeout = configuration.get(
            Constantes.ENV_MQ_BLOCKED_CONNECTION_TIMEOUT) or self.blocked_connection_timeout

    def __str__(self):
        return 'ConfigurationPika %s:%s' % (self.hostname, self.port)


class ConfigurationWebServer:

    def __init__(self):
        self.__port: Optional[int] = None

    def charger_env(self):
        self.__port = int(os.environ.get(Constantes.ENV_WEB_PORT) or '8080')

