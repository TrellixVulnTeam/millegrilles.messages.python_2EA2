import os

from typing import Optional

from millegrilles_messages.messages import Constantes as ConstantesMessages

CONST_BACKUP_PARAMS = [
    ConstantesMessages.ENV_CA_PEM,
    ConstantesMessages.ENV_CERT_PEM,
    ConstantesMessages.ENV_KEY_PEM,
    ConstantesMessages.ENV_MQ_HOSTNAME,
    ConstantesMessages.ENV_MQ_PORT,
]


class ConfigurationBackup:

    def __init__(self):
        self.ca_pem_path = '/var/opt/millegrilles/configuration/pki.millegrille.cert'
        self.cert_pem_path: Optional[str] = None
        self.key_pem_path: Optional[str] = None
        self.mq_host = 'localhost'
        self.mq_port = 5673

    def get_env(self) -> dict:
        """
        Extrait l'information pertinente de os.environ
        :return: Configuration dict
        """
        config = dict()
        for opt_param in CONST_BACKUP_PARAMS:
            value = os.environ.get(opt_param)
            if value is not None:
                config[opt_param] = value

        return config

    def parse_config(self, configuration: Optional[dict] = None):
        """
        Conserver l'information de configuration
        :param configuration:
        :return:
        """
        dict_params = self.get_env()
        if configuration is not None:
            dict_params.update(configuration)

        self.ca_pem_path = dict_params.get(ConstantesMessages.ENV_CA_PEM) or self.ca_pem_path
        self.cert_pem_path = dict_params.get(ConstantesMessages.ENV_CERT_PEM) or self.cert_pem_path
        self.key_pem_path = dict_params.get(ConstantesMessages.ENV_KEY_PEM) or self.key_pem_path
        self.mq_host = dict_params.get(ConstantesMessages.ENV_MQ_HOSTNAME) or self.mq_host
        self.mq_port = dict_params.get(ConstantesMessages.ENV_MQ_PORT) or self.mq_port
