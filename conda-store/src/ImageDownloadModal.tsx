import React from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

const ImageDownloadModal = (props: any) => {

return(
      <div>
      <Modal show={props.show} onHide={props.handleClose}>
        <Modal.Header>
          <Modal.Title>Environment Packaged Images</Modal.Title>
        </Modal.Header>
		<Modal.Body>
			These are images - one is an archive tarball and the other is a docker tarball. The docker image will allow you
			to build a copy of the environment within a new containeree to isolate. 
		</Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={props.handleClose}>
		  Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
	    }

export default ImageDownloadModal;
	
