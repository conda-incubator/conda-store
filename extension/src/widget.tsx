import { ReactWidget } from '@jupyterlab/apputils';
import 'bootstrap/dist/css/bootstrap.min.css';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Jumbotron from 'react-bootstrap/Jumbotron';
import BackendSelector from './backendSelector';
import React, { useState } from 'react';
import CardGroupComponent from './CardGroup';
import EnvironmentEditorPanel from './EnvironmentEditorPanel';
import BuildInformationPanel from './BuildInformationPanel';
import ImageDownloadModal from './ImageDownloadModal';
//import ErrorPanel from './ErrorPanel';
/**
 * React component for a counter.
 *
 * @returns The React component
 */
const HomeArea = (): JSX.Element => {
  const [serverAddress, setServerAddress] = useState(null); // Server Address String.
  const [toggleEnvironment, setToggleEnvironment] = useState(false); // Show/Hide the Env Panel
  const [toggleInfo, setToggleInfo] = useState(false);
  const [toggleCondaCards, setToggleCondaCards] = useState(true);
  const [toggleImageDl, setToggleImageDl] = useState(false);
  const [environmentData, setEnvironmentData] = useState(null);
  const [environmentHash, setEnvironmentHash] = useState(null);

 const servers = [
   {
     display_name: 'Local Filesystem',
     url: 'http://localhost:5000/api/v1/',
     url_build: 'http://localhost:5000/api/v1/build/',
   },
   {},
 ];

	
 function handleSetEnvironmentData(data: any) {
   setEnvironmentData(data);
   console.log(environmentData);
 }

  function handleServerSelect(e: any) {
    e.preventDefault(); //Prevent a reload
    //TODO: Find a way to figure out which index was selected
    //TODO: Write script to check connections - for now, assuming connection
    setServerAddress(servers[0].url);
    setToggleCondaCards(true);
   }
 
  /*
   * Handles the edit environment button click
   */
 function handleEditEnv(e: any, name: string) {
    e.preventDefault(); //Prevent a reload
    setToggleEnvironment(true); //
    setToggleCondaCards(false);
    const ed = environmentData.find((e: any) => e.name == name);
    const hash = ed.specification.sha256;
    setEnvironmentHash(hash);
  }

  /*
   * Handles a click on "Build Specification"
   */
  function handleInfoClick(e: any) {
    e.preventDefault(); //Prevent a reload
    setToggleInfo(true); //
    setToggleCondaCards(false);
  }

  /*
   * Handles a click on Image
   */
  function handleImageClick(e: any) {
    e.preventDefault(); //Prevent a reload
    setToggleImageDl(true);
  }
  
  function handleImageCancel(e: any) {
    e.preventDefault(); //Prevent a reload
    setToggleImageDl(false);
  }
  
  /*
   * Handles a "Cancel"
   */
  function handleCancel(e: any) {
    e.preventDefault();
    setToggleImageDl(false);
    setToggleInfo(false);
    setToggleEnvironment(false);
    setToggleCondaCards(true);
  }

  return (
      <div>
      {serverAddress ? (
        <div>
            {toggleCondaCards ? (
                  <CardGroupComponent
		    setEnvData={handleSetEnvironmentData}
                    url={serverAddress+'/environment/'}
                    handleEditEnvClick={handleEditEnv}
                    handleInfoClick={handleInfoClick}
                    handleImageClick={handleImageClick}
                  />
            ) : null}

            {toggleEnvironment ? (
              <div>
                <EnvironmentEditorPanel
                  url={serverAddress+'/specification/'}
		  hash={environmentHash}
                  handleCancelClick={handleCancel}
                />
              </div>
            ) : null}

            {toggleInfo ? (
              <div>
                <BuildInformationPanel
                  url={servers[0].url_build}
                  build_no="1"
                />
              </div>
            ) : null}
		      {toggleImageDl ? <div>
			      <ImageDownloadModal
				      show={toggleImageDl}
				      handleClose={handleImageCancel}
				      />
			      </div> : null}
        </div>
      ) :
          <Row
            className="justify-content-center align-items-center"
            style={{ height: '100vh' }}
          >
            <Col xs={4} sm={6} md={8} className="my-auto">
              <Jumbotron>
                <h1> Welcome to Conda-Store </h1>
                <BackendSelector
                  handleServerSelect={handleServerSelect}
                  serverConnectionData={servers}
                />
              </Jumbotron>
            </Col>
          </Row>
      }
    </div>
  );
};
/**
 * A Counter Lumino Widget that wraps a CounterComponent.
 */
//const CondaStoreWidget: Widget = ReactWidget.create(
//);
export class CondaStoreWidget extends ReactWidget {
  /**
   * Constructs a new CounterWidget.
   */
  constructor() {
    super();
    this.addClass('jp-ReactWidget');
  }

  render(): JSX.Element {
    return (
 <div>
   <HomeArea />
 </div>
    )
  }
}
