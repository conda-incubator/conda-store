import asyncio
import json
import os

from conda_store.api import CondaStoreAPI
from jupyterhub.auth import DummyAuthenticator
from jupyterhub.spawner import SimpleLocalProcessSpawner
from jupyterhub.utils import maybe_future


c.JupyterHub.ip = "0.0.0.0"

c.JupyterHub.authenticator_class = DummyAuthenticator
c.DummyAuthenticator.password = 'test'


class CondaStoreSpawner(SimpleLocalProcessSpawner):
    async def options_form(self, spawner):
        token = await self.generate_token(spawner.user.name)
        environments = await self.list_environments(token)
        options = [f'<option value="{_["current_build_id"]}" {"selected" if i == 0 else ""}>{_["namespace"]["name"]}/{_["name"]}</option>' for i,_ in enumerate(environments)]

        return f'''
conda-store environment must contain jupyterhub, jupyterlab, nb_conda_store_kernels, and jupyterlab

Choose an environment:
<select name="build_id" multiple="false">
{''.join(options)}
</select>
'''

    async def options_from_form(self, form_data):
        return {key: value[0] for key, value in form_data.items()}

    async def start(self):
        self.conda_store_token = await self.generate_token(self.user.name)
        self.cmd = ['/opt/conda/envs/conda-store/bin/conda-store', 'run', self.user_options['build_id'], '--', 'jupyter-labhub']
        self.args = ['--JupyterApp.kernel_spec_manager_class', 'nb_conda_store_kernels.manager.CondaStoreKernelSpecManager']
        return await super().start()

    def user_env(self, env):
        env = super().user_env(env)
        env['CONDA_STORE_URL'] = "https://conda-store.localhost/conda-store"
        env['CONDA_STORE_AUTH'] = "token"
        env['CONDA_STORE_NO_VERIFY'] = "true"
        env['CONDA_STORE_TOKEN'] = self.conda_store_token
        return env

    async def generate_token(self, username):
        async with CondaStoreAPI(
                conda_store_url=os.environ['CONDA_STORE_URL'],
                auth_type=os.environ['CONDA_STORE_AUTH'],
                verify_ssl='CONDA_STORE_NO_VERIFY' not in os.environ) as conda_store:
            return await conda_store.create_token(
                primary_namespace=username,
                role_bindings={
                    'default/*': ['viewer'],
                    f'{username}/*': ['admin'],
                }
            )

    async def list_environments(self, token: str):
        async with CondaStoreAPI(
                conda_store_url=os.environ['CONDA_STORE_URL'],
                auth_type=os.environ['CONDA_STORE_AUTH'],
                verify_ssl='CONDA_STORE_NO_VERIFY' not in os.environ) as conda_store:
            return await conda_store.list_environments(
                status='COMPLETED',
                artifact='CONDA_PACK',
                packages=['jupyterhub', 'jupyterlab', 'ipykernel', 'nb_conda_store_kernels'])

c.JupyterHub.spawner_class = CondaStoreSpawner

c.JupyterHub.services = [
    {
        'name': "conda-store",
        'oauth_client_id': "service-this-is-a-jupyterhub-client",
        'admin': True,
        'url': 'https://conda-store.localhost/conda-store/',
        'api_token': "this-is-a-jupyterhub-secret",
        'oauth_redirect_uri': '/conda-store/oauth_callback/',
        'oauth_no_confirm': True, # allows no authorize yes/no button
    }
]
