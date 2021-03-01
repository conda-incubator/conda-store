import React from 'react';
import AceEditor from 'react-ace';

import 'ace-builds/src-noconflict/mode-yaml';
import 'ace-builds/src-noconflict/theme-solarized_light';
import 'ace-builds/src-noconflict/ext-language_tools';

const TextEditor = (props: any) => {
  function onChange(newValue: any) {
    console.log('change', newValue);
  }

  return (
    <AceEditor
      mode="yaml"
      fontSize={18}
      theme="solarized_light"
      onChange={onChange}
      name="UNIQUE_ID_OF_DIV"
      value={props.yaml_spec}
      editorProps={{}}
      setOptions={{
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: true,
      }}
    />
  );
};

export default TextEditor;
