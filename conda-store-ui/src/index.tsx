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

interface Spec {
  name: string
  current?: number
  default?: number
  options?: number[]
  request?: number
}

const specRef: Spec[] = [
  {
    name: "dask",
    current: 14.37,
    default: 15,
    options: [1.00, 2.00, 14.37, 15],
  },
  {
    name: "numpy",
    current: 1.99,
    default: 1.99,
    options: [1.00, 1.10, 1.99],
  },
  {
    name: "pandas",
    default: 69.420,
    options: [13.00, 14.10, 69.420],
  },
  {
    name: "spark",
    default: 1024.00,
    options: [36.00, 47.10, 1024.00],
  },
];

const specMap = new Map<string, Spec>(specRef.map(x => [x.name, x]));

const getNameOptions: () => string[] = () => specRef.map(x => x.name);
const getSpec = (name: string | null) => name === null || !specMap.has(name) ? null : {...specMap.get(name)!};
const getVersionOptions: (name: string) => number[] = name => specMap.get(name)?.options ?? [];

export function PackagePickerList() {
  const [specs, setSpecs] = React.useState<(Spec | null)[]>([null]);

  const onSpecChange = (newSpec: Spec | null, ix?: number) => {
    specs.splice(ix ?? specs.length, 1, newSpec);
    setSpecs([...specs]);
  }
  const addSpec = () => {onSpecChange(null);}

  return (
    <Stack>
    {specs.map((x, i) =>
      <PackagePickerItem
        ix={i}
        key={i}
        onSpecChange={onSpecChange}
        spec={x}
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
  spec: Spec | null,
  ix: number,
  onSpecChange: (newSpec: Spec | null, key: number) => void,
}) {
  return (
    <Stack direction="row">
      <Autocomplete
        onChange={(event: any, name: string | null) => {
          params.onSpecChange(getSpec(name), params.ix)
        }}
        options={getNameOptions()}
        renderInput={(params) => <TextField {...params} label="Pkg Name" />}
        sx = {{minWidth: 300}}
        value={params.spec?.name ?? null}
      />
      <Autocomplete
        disabled={params.spec === null}
        getOptionLabel={option => option?.toString() ?? ""}
        onChange={(event: any, version?: number) => {
          if (params.spec !== null) {
            params.onSpecChange({...params.spec, current: version}, params.ix)
          }
        }}
        options={params.spec === null ? [] : getVersionOptions(params.spec.name)}
        renderInput={(params) => <TextField {...params} label="Pkg Version" />}
        sx = {{minWidth: 150}}
        value={params.spec === null || params.spec.current === null ? null : params.spec.current ?? params.spec.default ?? params.spec.options?.at(-1)}
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

root.render(<PackagePickerList/>);
