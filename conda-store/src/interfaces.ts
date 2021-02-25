export interface IEnv {
  /* The name of the environment */
  name: string;
  /* The build number of the environment (essentially, the revision number) */
  namespace: string;
  build_id: number;
  /* The size of the environment in bytes */
  size?: number;
  /* The sha-256 specification of the build. */
  specification: string;
  /* The path to the store */
  store_path?: string;
  /* OPT/TODO: Jupyter Kerenel JSON Parse metadata */
  jupyter_kernel?: string;
  /* OPT: A string that describes the env*/
  conda_desc?: string;
  /* OPT: A single string to describe the environment's name in jupyter */
  jupyter_desc?: string;
}

