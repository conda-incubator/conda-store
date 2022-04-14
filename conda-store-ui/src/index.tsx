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
  name: string | null
  current: number | null
  request: number | null
}

const nameOptions = ["numpy", "pandas"];
const versionInfo = {
  dask: {
    current: 14.37,
    default: 15,
    options: [1.00, 2.00, 14.37, 15],
  },
  numpy: {
    current: 1.99,
    default: 1.99,
    options: [1.00, 1.10, 1.99],
  },
  pandas: {
    default: 1.99,
    options: [1.00, 1.10, 1.99],
  },
  spark: {
    default: 1.99,
    options: [1.00, 1.10, 1.99],
  },

};

const getNameOptions = () => nameOptions;
const getVersionDefault = (name: string) => versionInfo[name as keyof typeof versionInfo].default;
const getVersionCurrent = (name: string) => versionInfo[name as keyof typeof versionInfo].current ?? null;
const getVersionOptions = (name: string) => versionInfo[name as keyof typeof versionInfo].options;

export function PackagePickerList() {
  const [specs, setSpecs] = React.useState<Spec[]>([{name: null, current: null, request: null}]);

  const onSpecChange = (newSpec: Spec, ix?: number) => {
    specs.splice(ix ?? specs.length, 1, newSpec);
    setSpecs([...specs]);
  }

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
        onClick={() => onSpecChange({name: null, current: null, request: null})}
        sx={{width: 24}}
      >
        <PlusIcon/>
      </IconButton>
    </Stack>
  );
}

export function PackagePickerItem(params: {
  spec: Spec,
  ix: number,
  onSpecChange: (newSpec: Spec, key: number) => void,
}) {
  return (
    <Stack direction="row">
      <Autocomplete
        onChange={(event: any, name: string | null) => {
          params.onSpecChange({name, current: name === null ? null : getVersionDefault(name)}, params.ix)
        }}
        options={getNameOptions()}
        renderInput={(params) => <TextField {...params} label="Pkg Name" />}
        sx = {{minWidth: 300}}
        value={params.spec.name}
      />
      <Autocomplete
        disabled={!params.spec.name}
        onChange={(event: any, version: number | null) => {
          params.onSpecChange({name: params.spec.name, current: version}, params.ix)
        }}
        options={params.spec.name === null ? [] : getVersionOptions(params.spec.name)}
        renderInput={(params) => <TextField {...params} label="Pkg Version" />}
        sx = {{minWidth: 150}}
        value={params.spec.name === null ? null : params.spec.current}
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

export function PackagePicker() {
  const [nameValue, setNameValue] = React.useState<string | null>(null);

  const [versionDisabled, setVersionDisabled] = React.useState<boolean>(true);
  const [versionOptions, setVersionOptions] = React.useState<number[]>([]);
  const [versionValue, setVersionValue] = React.useState<number | null>(null);

  const onNameChange = (event: any, newValue: string | null) => {
    setNameValue(newValue);

    if (newValue !== null) {
      setVersionDisabled(false);
      setVersionOptions(versionInfo[newValue as keyof typeof versionInfo].options);
      setVersionValue(versionInfo[newValue as keyof typeof versionInfo].default);
    } else {
      setVersionDisabled(true);
      setVersionOptions([]);
      setVersionValue(null);
    }
  }

  return (
    <Stack direction="row">
      <Autocomplete
        onChange={onNameChange}
        options={nameOptions}
        renderInput={(params) => <TextField {...params} label="Pkg Name" />}
        sx = {{minWidth: 300}}
        value={nameValue}
      />
      <Autocomplete
        disabled={versionDisabled}
        onChange={(event: any, newValue: number | null) => {
          setVersionValue(newValue);
        }}
        options={versionOptions}
        renderInput={(params) => <TextField {...params} label="Pkg Version" />}
        sx = {{minWidth: 150}}
        value={versionValue}
      />
    </Stack>
  );
}

const rootElem = document.createElement("div");
document.body.appendChild(rootElem);
const root = createRoot(rootElem);

root.render(<PackagePickerList/>);
