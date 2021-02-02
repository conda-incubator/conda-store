import React, { useState, useEffect } from 'react';
import { IEnv } from './interfaces';
import CondaCard from './CondaCard';

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
  }, []);

  return (
    <div>
      {showCondaCards
        ? envdata.map((envData: IEnv) => (
            <CondaCard
              envInfo={envData}
              handleBuildClick={props.handleBuildClick}
              handleEditEnvClick={props.handleEditEnvClick}
              handleInfoClick={props.handleInfoClick}
              handleImageClick={props.handleImageClick}
            />
          ))
        : null}
    </div>
  );
};

export default CardGroupComponent;
