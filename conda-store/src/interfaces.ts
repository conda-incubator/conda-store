export interface IEnvSpecificationSpec {
	channels: [string];
	dependencies: [string];
	name: string;
	prefix?: string;
} 

export interface IEnvSpecification {
	id: number;
	created_on: string; /* TODO: figure out how to handle datetime */
	name: string;
	sha256: string;
	spec?: {
		[key: string]: IEnvSpecificationSpec
	};
}


export interface IEnv {
  /* The name of the environment */
  name: string;
  /* The build number of the environment (essentially, the revision number) */
  id: number;
  /* namespace of the environment */
  namespace: string;
  /* The sha-256 specification of the build. */
  specification?: { 
	  [key: string]: IEnvSpecification
  };
  /* The path to the store */
  store_path?: string;
  /* OPT/TODO: Jupyter Kerenel JSON Parse metadata */
  jupyter_kernel?: string;
  /* OPT: A string that describes the env*/
  conda_desc?: string;
  /* OPT: A single string to describe the environment's name in jupyter */
  jupyter_desc?: string;
}

