import React from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';

const BackendSelector = (props: any) => {
  return (
    <div>
      <h6>
        {' '}
        Please select an appropriate backend you would like to connect to:{' '}
      </h6>
      <Form.Control as="select">
        <option> {props.serverConnectionData[0].display_name || null} </option>
      </Form.Control>
      <ButtonToolbar className="mt-2 justify-content-end">
        <Button
          variant="success"
          type="submit"
          onClick={(e) => props.handleServerSelect(e)}
        >
          Connect
        </Button>{' '}
      </ButtonToolbar>
    </div>
  );
}

export default BackendSelector;
