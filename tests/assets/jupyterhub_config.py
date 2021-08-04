c.JupyterHub.ip = "0.0.0.0"

c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = 'test'

c.Spawner.cmd=["jupyter-labhub"]
c.JupyterHub.spawner_class = 'jupyterhub.spawner.SimpleLocalProcessSpawner'
