import React, { useState, useEffect } from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import Jumbotron from 'react-bootstrap/Jumbotron';

const BuildInformationPanel = (props: any) => {
  const [buildInformation, setBuildInformation] = useState(null);
  useEffect(() => {
    const getBuildData = async () => {
      const response = await fetch(props.url + props.build_no);
      const jsondata = await response.json();
      console.log(jsondata);
      setBuildInformation(jsondata);
    };
    getBuildData();
  }, []);

  return (
    <div style={{ marginTop: '2rem' }}>
      <Container fluid>
        {buildInformation ? (
          <Jumbotron>
            <h6>
              {' '}
              Build <small className="text-muted">1</small>
            </h6>
            <h6> Path {buildInformation.archive_path} </h6>
            <h6> Finished Building: {buildInformation.ended_on} </h6>
          </Jumbotron>
        ) : null}
        <Row>
          <Col>
            <Table striped bordered hover>
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Version</th>
                </tr>
              </thead>
              <tbody>
                {buildInformation
                  ? buildInformation.packages.map((pacakgeinfo: any) => (
                      <tr>
                        <td>{pacakgeinfo.name}</td>
                        <td>{pacakgeinfo.version}</td>
                      </tr>
                    ))
                  : null}
              </tbody>
            </Table>
          </Col>
        </Row>
      </Container>
    </div>
  );
};
export default BuildInformationPanel;
