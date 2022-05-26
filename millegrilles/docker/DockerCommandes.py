import base64
import json

from typing import Union

from docker import DockerClient

from millegrilles.docker.DockerHandler import CommandeDocker


class CommandeListerContainers(CommandeDocker):

    def __init__(self, callback=None, aio=False, filters: dict = None):
        super().__init__(callback, aio)
        self.__filters = filters

    def executer(self, docker_client: DockerClient):
        liste = docker_client.containers.list(filters=self.__filters)
        self.callback(liste)

    async def get_liste(self) -> list:
        resultat = await self.attendre()
        liste = resultat['args'][0]
        return liste


class CommandeListerServices(CommandeDocker):

    def __init__(self, callback=None, aio=False, filters: dict = None):
        super().__init__(callback, aio)
        self.__filters = filters

    def executer(self, docker_client: DockerClient):
        liste = docker_client.services.list(filters=self.__filters)
        self.callback(liste)

    async def get_liste(self) -> list:
        resultat = await self.attendre()
        liste = resultat['args'][0]
        return liste


class CommandeAjouterConfiguration(CommandeDocker):

    def __init__(self, nom: str, data: Union[dict, str, bytes], labels: dict = None, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__nom = nom
        self.__labels = labels

        if isinstance(data, dict):
            data_string = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_string = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_string = data
        else:
            raise ValueError("Type data non supporte")

        self.__data = data_string

    def executer(self, docker_client: DockerClient):
        reponse = docker_client.configs.create(name=self.__nom, data=self.__data, labels=self.__labels)
        self.callback(reponse)

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]


class CommandeSupprimerConfiguration(CommandeDocker):

    def __init__(self, nom: str, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__nom = nom

    def executer(self, docker_client: DockerClient):
        config = docker_client.configs.get(self.__nom)
        reponse = config.remove()
        self.callback(reponse)

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]


class CommandeGetConfiguration(CommandeDocker):

    def __init__(self, nom: str, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__nom = nom

    def executer(self, docker_client: DockerClient):
        config = docker_client.configs.get(self.__nom)
        self.callback(config)

    async def get_config(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]

    async def get_data(self) -> str:
        resultat = await self.attendre()
        config = resultat['args'][0]
        data = config.attrs['Spec']['Data']
        data_str = base64.b64decode(data)
        if isinstance(data_str, bytes):
            data_str = data_str.decode('utf-8')

        return data_str


class CommandeAjouterSecret(CommandeDocker):

    def __init__(self, nom: str, data: Union[dict, str, bytes], labels: dict = None, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__nom = nom
        self.__labels = labels

        if isinstance(data, dict):
            data_string = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_string = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_string = data
        else:
            raise ValueError("Type data non supporte")

        self.__data = data_string

    def executer(self, docker_client: DockerClient):
        reponse = docker_client.secrets.create(name=self.__nom, data=self.__data, labels=self.__labels)
        self.callback(reponse)

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]


class CommandeSupprimerSecret(CommandeDocker):

    def __init__(self, nom: str, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__nom = nom

    def executer(self, docker_client: DockerClient):
        config = docker_client.secrets.get(self.__nom)
        reponse = config.remove()
        self.callback(reponse)

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]


class CommandeCreerService(CommandeDocker):

    def __init__(self, configuration: dict, callback=None, aio=False):
        super().__init__(callback, aio)
        self.__configuration = configuration

    def executer(self, docker_client: DockerClient):
        config = docker_client.secrets.get(self.__nom)
        reponse = config.remove()
        self.callback(reponse)

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]


class CommandeGetConfigurationsDatees(CommandeDocker):
    """
    Fait la liste des config et secrets avec label certificat=true et password=true
    """
    def __init__(self, callback=None, aio=False):
        super().__init__(callback, aio)

    def executer(self, docker_client: DockerClient):

        dict_secrets = dict()
        dict_configs = dict()

        reponse = docker_client.secrets.list(filters={'label': 'certificat=true'})
        dict_secrets.update(self.parse_reponse(reponse))

        reponse = docker_client.secrets.list(filters={'label': 'password=true'})
        dict_secrets.update(self.parse_reponse(reponse))

        reponse = docker_client.configs.list(filters={'label': 'certificat=true'})
        dict_configs.update(self.parse_reponse(reponse))

        correspondance = self.correspondre_cle_cert(dict_secrets, dict_configs)

        self.callback({'configs': dict_configs, 'secrets': dict_secrets, 'correspondance': correspondance})

    def parse_reponse(self, reponse) -> dict:
        data = dict()

        for r in reponse:
            r_id = r.id
            name = r.name
            attrs = r.attrs
            labels = attrs['Spec']['Labels']
            data[name] = {'id': r_id, 'name': name, 'labels': labels}

        return data

    def correspondre_cle_cert(self, dict_secrets: dict, dict_configs: dict):

        dict_correspondance = dict()
        self.__mapper_params(dict_correspondance, list(dict_secrets.values()), 'key')
        self.__mapper_params(dict_correspondance, list(dict_configs.values()), 'cert')

        # Ajouter key "current" pour chaque certificat
        for prefix, dict_dates in dict_correspondance.items():
            sorted_dates = sorted(dict_dates.keys(), reverse=True)
            dict_dates['current'] = dict_dates[sorted_dates[0]]

        return dict_correspondance

    def __mapper_params(self, dict_correspondance: dict, vals: list, key_param: str):
        for v in vals:
            if v['labels']['certificat'] == 'true':
                prefix = v['labels']['label_prefix']
                v_date = v['labels']['date']
                try:
                    dict_prefix = dict_correspondance[prefix]
                except KeyError:
                    dict_prefix = dict()
                    dict_correspondance[prefix] = dict_prefix

                try:
                    dict_date = dict_prefix[v_date]
                except KeyError:
                    dict_date = dict()
                    dict_prefix[v_date] = dict_date

                dict_date[key_param] = {'name': v['name'], 'id': v['id']}

    async def get_resultat(self) -> list:
        resultat = await self.attendre()
        return resultat['args'][0]
