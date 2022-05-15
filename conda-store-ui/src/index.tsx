/*
 * Copyright (c) 2020, Max Klein
 *
 * This file is part of the tree-finder library, distributed under the terms of
 * the BSD 3 Clause license. The full license can be found in the LICENSE file.
 */
import * as React from "react"
import {createRoot} from "react-dom/client";
import Autocomplete from "@mui/material/Autocomplete";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import SvgIcon from "@mui/material/SvgIcon";
import TextField from "@mui/material/TextField";

interface PkgRef {
  name: string
  version: number
}

interface PkgRecord {
  name: string
  version?: number
  explicit?: boolean
}

const buildCurrents: PkgRecord[] = [
  {name: "dask", version: 14.37, explicit: true},
  {name: "numpy", version: 1.99},
  {name: "fsspec", version: 0.70},
]

// const packagesRef: Package[] = [
//   ["dask", [1.00, 2.00, 14.37, 15.00]],
//   ["jupyterlab", [1.00, 2.00, 3.00, 3.30]],
//   ["jupyter_core", [1.00, 6.00, 7.00]],
//   ["jupyter_server", [0.90, 1.00, 1.10]],
//   ["numpy", [1.00, 1.10, 1.99]],
//   ["pandas", [13.00, 14.10, 69.420]],
//   ["spark", [36.00, 47.10, 1024.00]],
// ].map(([name, vers]: [string, number[]]) => vers.map(ver => {return {name, version: ver}})).flat();

const pkgRefs: PkgRef[] = [
  { name: 'dask', version: 1.00 },
  { name: 'dask', version: 2.00 },
  { name: 'dask', version: 14.37 },
  { name: 'dask', version: 15.00 },
  { name: 'fsspec', version: 0.60 },
  { name: 'fsspec', version: 0.70 },
  { name: 'jupyterlab', version: 1.00 },
  { name: 'jupyterlab', version: 2.00 },
  { name: 'jupyterlab', version: 3.00 },
  { name: 'jupyterlab', version: 3.30 },
  { name: 'jupyter_core', version: 1.00 },
  { name: 'jupyter_core', version: 6.00 },
  { name: 'jupyter_core', version: 7.00 },
  { name: 'jupyter_server', version: 0.90 },
  { name: 'jupyter_server', version: 1.00 },
  { name: 'jupyter_server', version: 1.10 },
  { name: 'numpy', version: 1.00 },
  { name: 'numpy', version: 1.10 },
  { name: 'numpy', version: 1.99 },
  { name: 'pandas', version: 13.00 },
  { name: 'pandas', version: 14.10 },
  { name: 'pandas', version: 69.42 },
  { name: 'spark', version: 36.00 },
  { name: 'spark', version: 47.10 },
  { name: 'spark', version: 1024.00 }
]

const getPackageRefNames = () => [...new Set(pkgRefs.map(x => x.name))];
const getPackageBuildNames = (vis?: "explicit" | "implicit") => {
  let pkgs = [...buildCurrents];
  if (vis === "explicit") {
    pkgs = pkgs.filter(x => x.explicit === true);
  } else if (vis === "implicit") {
    pkgs = pkgs.filter(x => x.explicit !== true);
  }
  return pkgs.map(x => x.name);
};
const getPackageInstallableNames = () => getPackageRefNames().filter(x => !getPackageBuildNames().includes(x));

// this works since Map.set returns the Map object
const getVersions = (pkgs: PkgRef[]) => pkgs.reduce((map, pkg) => map.set(pkg.name, [...map.get(pkg.name) ?? [], pkg.version]), new Map<string, number[]>());
const getModels = (pkgs: PkgRef[]) => new Map(pkgs.map(x => [x.name, x]));

const pkgVersions = getVersions(pkgRefs);
const pkgModels = getModels(pkgRefs);

interface ItemModel {
  name: string,
  current?: number,
  future?: number,
  explicit?: boolean,
}

export function PackagePickerList(params: {
  currents?: PkgRecord[],
  futures?: PkgRecord[],
}) {
  const [futures, setFutures] = React.useState<PkgRecord[]>(params.futures ?? [{name: "", explicit: true}]);

  const currents = params.currents ?? [];
  const currentsMap = new Map<string, PkgRecord>(currents.map(x => [x.name, x]));

  const initModels = () => {
    const futuresMap = new Map<string, PkgRecord>(futures.map(x => [x.name, x]));
    const items: ItemModel[] = [];

    for (const c of currents) {
      const f = futuresMap.get(c.name);

      items.push({
        name: c.name,
        current: c.version,
        future: f?.version,
        explicit: f?.explicit || c.explicit,
      });
    }

    for (const f of futures) {
      if (!currentsMap.has(f.name)) {
        items.push({
          name: f.name,
          future: f.version,
          explicit: f.explicit,
        });
      }
    }

    return items;
  }

  const onFutureChange = (future?: PkgRecord, ix?: number) => {
    ix = ix ? ix - currents.length : futures.length;

    if (future) {
      futures.splice(ix, 1, future);
    } else {
      futures.splice(ix, 1);
    }

    setFutures([...futures]);
  }

  const addSpec = () => {onFutureChange({name: "", explicit: true});}

  const items = initModels();

  return (
    <Stack>
    {items.map((x, i) =>
      <PackagePickerItem
        ix={i}
        key={i}
        onFutureChange={onFutureChange}
        model={x}
      />
    )}
      <IconButton
        onClick={addSpec}
        sx={{width: 24}}
      >
        <PlusIcon/>
      </IconButton>
    </Stack>
  );
}

export function PackagePickerItem(params: {
  model: ItemModel,
  ix: number,
  onFutureChange: (future?: PkgRecord, ix?: number) => void,
}) {
  return (
    <Stack direction="row">
      <Autocomplete
        disabled={!!params.model.current}
        onChange={(event: any, name?: string) => {
          if (name !== params.model.name) {
            params.onFutureChange({name: name || "", explicit: true}, params.ix);
          }
        }}
        options={[...getPackageInstallableNames(), ""]}
        renderInput={(params) => <TextField {...params} label="name" />}
        sx = {{minWidth: 300}}
        value={params.model.name ?? null}
      />
      <Autocomplete
        disabled={true}
        options={[]}
        renderInput={(params) => <TextField {...params} label="current version" />}
        sx = {{minWidth: 150}}
        value={params.model.current ?? null}
      />
      <Autocomplete
        disabled={!params.model.name}
        getOptionLabel={option => option?.toString() ?? ""}
        onChange={(event: any, version?: number) => {
          if (version != params.model.future) {
            params.onFutureChange({...params.model, version}, params.ix);
          }
        }}
        options={pkgVersions.get(params.model.name)?.filter(x => x !== params.model.current) ?? []}
        renderInput={(params) => <TextField {...params} label="version request" />}
        sx = {{minWidth: 150}}
        value={params.model.future ?? null}
      />
    </Stack>
  );
}

export function PlusIcon() {
  return (
    <SvgIcon xmlns="http://www.w3.org/2000/svg" width="16" viewBox="0 0 24 24">
      <g fill="#616161">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
      </g>
    </SvgIcon>
  )
}

const rootElem = document.createElement("div");
document.body.appendChild(rootElem);
const root = createRoot(rootElem);

root.render(<PackagePickerList
  currents={buildCurrents}
/>);
