import React from 'react';
import Button from 'react-bootstrap/Button';



const ErrorPanel = (props: any) => {
	return (
		<div>
			<h6>
				{' '}
				Unfortunatley, an error has occured. Please check the console for 
				more information, or create an <a href='https://github.com/Quansight/conda-store'>issue</a>
			</h6>
			<Button
				 variant="warning">Go Back</Button>{' '}
		</div>
	);
}

export default ErrorPanel;
