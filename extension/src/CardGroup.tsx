import React, { useState } from 'react';
import { IEnv } from './interfaces';
import CondaCard from './CondaCard';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';

/**
 * React component for a group of conda card generated from an array.
 *
 * @returns The React component
 */
const CardGroupComponent = (props: any) => {
//  const [envdata, setEnvdata] = useState(null);
  const [showCondaCards] = useState(true);

//  useEffect(() => {
//    const renderCondaCards = async () => {
//      const response = await fetch(props.url);
//      const jsondata = await response.json();
//      setEnvdata(jsondata);
//      setShowCondaCards(true);
//    };
//    renderCondaCards();
//  }, [
//	  envdata
//  ]);
//
  return (
    <div>
	    <Container fluid="md">
		    <Row>
      {showCondaCards
	      ? props.envdata.map((envData: IEnv) => (
		      <Col md={6}>
            <CondaCard
              envInfo={envData}
              handleEditEnvClick={props.handleEditEnvClick}
              handleInfoClick={props.handleInfoClick}
              handleImageClick={props.handleImageClick}
            />

		      </Col>
          ))
        : null}
		    </Row>
	    </Container>
    </div>
  );
};

export default CardGroupComponent;
