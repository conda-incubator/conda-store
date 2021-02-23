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
  const [envdata, setEnvdata] = useState(null);
  const [showCondaCards, setShowCondaCards] = useState(false);

  useEffect(() => {
    const renderCondaCards = async () => {
      const response = await fetch(props.url);
      const jsondata = await response.json();
      setEnvdata(jsondata);
      setShowCondaCards(true);
    };
    renderCondaCards();
  }, [
	  envdata
  ]);
//  let test_card: IEnv = {
//	  name: "test",
//	  build_id: 4,
//	  size: 220,
//	  specification: "lol3ssdf32wef",
//	  store_path: "/the/path/to/the/store",
//  }

  return (
    <div>
	    <Container fluid="md">
		    <Row>
      {showCondaCards
	      ? envdata.map((envData: IEnv) => (
		      <Col md={6}>
            <CondaCard
              envInfo={envData}
              handleBuildClick={props.handleBuildClick}
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
