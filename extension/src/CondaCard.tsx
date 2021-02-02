import React from 'react';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';
import {
  faCog,
  faEdit,
  faFileArchive,
  faInfoCircle,
} from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

/**
 * This will be the media card that shows the conda environment information
 * It will show:
 * The Environment Name
 * Docker Build Tags Link
 * Specifications Link
 * A special _jupyter_ name, to link it to the KernelMap
 */
const CondaCard = (props: any) => {
  let sizemb = Math.round(props.envInfo.size * 10 ** -6) + 'MB';
  return (
    <Card
      style={{
        width: '24rem',
        marginTop: '2rem',
        marginBottom: '2rem',
      }}
    >
      <Card.Body>
        <Card.Title>{props.envInfo.name}</Card.Title>
        <Card.Subtitle className="mb-2 text-info">
          Size: {sizemb || null}
        </Card.Subtitle>
        <Card.Text>
          {props.envInfo.conda_desc ||
            'Some quick example text to build on the card title and make up the bulk of the card content.'}
        </Card.Text>
      </Card.Body>
      <Card.Footer>
        <ButtonToolbar className="mb-2 ml-5 mr-5 justify-content-between">
          <Button
            variant="primary"
            onClick={(e) => {
              props.handleEditEnvClick(e);
              props.handleBuildClick(props.envInfo.spec_sha256);
            }}
          >
            <FontAwesomeIcon icon={faEdit} /> Edit
          </Button>{' '}
          <Button variant="outline-primary">
            Display <FontAwesomeIcon icon={faCog} />
          </Button>{' '}
        </ButtonToolbar>
        <ButtonToolbar className="mb-2 ml-5 mr-5 justify-content-between">
          <Button variant="info" onClick={(e) => props.handleInfoClick(e)}>
            <FontAwesomeIcon icon={faInfoCircle} /> Info
          </Button>{' '}
          <Button
            variant="secondary"
            onClick={(e) => props.handleImageClick(e)}
          >
            <FontAwesomeIcon icon={faFileArchive} /> Images
          </Button>{' '}
        </ButtonToolbar>
      </Card.Footer>
    </Card>
  );
};

export default CondaCard;
