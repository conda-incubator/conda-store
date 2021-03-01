import React, { useState, useEffect } from 'react';
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
  //const [envdata, setEnvdata] = useState(null);
  const [showCondaCards, setShowCondaCards] = useState(false);
  const [cardData, setCardData] = useState(null);

  useEffect(() => {
   const renderCondaCards = async () => {
      const response = await fetch(props.url);
      const jsondata = await response.json();
      setCardData(jsondata);
      setShowCondaCards(true);
      props.setEnvData(jsondata);
    };

  const timeout = setTimeout(() => {
    renderCondaCards(); 
  }, 3000);


  return () => clearTimeout(timeout);
  }, [
	 cardData, 
	 props.setEnvData
  ]);

  return (
    <div>
	    <Container fluid="md">
		    <Row>
      {showCondaCards
	      ? cardData.map((envData: IEnv) => (
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
