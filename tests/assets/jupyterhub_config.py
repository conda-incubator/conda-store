c.JupyterHub.ip = "0.0.0.0"

c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = 'test'

c.Spawner.cmd=["jupyter-labhub"]
c.JupyterHub.spawner_class = 'jupyterhub.spawner.SimpleLocalProcessSpawner'

c.JupyterHub.services = [
    {
        'name': "conda-store",
        'oauth_client_id': "service-this-is-a-jupyterhub-client",
        'admin': True,
        'api_token': "this-is-a-jupyterhub-secret",
        'oauth_redirect_uri': 'http://localhost:5000/conda-store/oauth_callback/',
    }
]
