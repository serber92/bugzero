import React from 'react';
import { useHistory } from 'react-router-dom';

import PropTypes from 'prop-types';
import LoaderButton from '../../loader-button/LoaderButton';
import { Col, Button, Row, FormGroup } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

export default function ProductActions({ isLoading, handleDelete, handleSave, handleSaveAndAdd, vendorId, productId }) {
  const history = useHistory();

  return (
    <>
      <Row className="flex-between-center" style={{ marginTop: '40px' }}>
        <Col xs="4">
          <FormGroup>
            <Button block color="falcon-danger" onClick={() => history.push(`/vendors/${vendorId}/products`)}>
              Cancel
            </Button>
          </FormGroup>
        </Col>
        <Col xs="4">
          <FormGroup>
            {vendorId === 'hpe' ? (
              <LoaderButton block color="falcon-primary" name="" isLoading={isLoading} onClick={handleSaveAndAdd}>
                Save and add another
              </LoaderButton>
            ) : null}
          </FormGroup>
        </Col>
        <Col xs="4">
          <FormGroup>
            <LoaderButton block color="falcon-primary" onClick={handleSave} name="save-and-add" isLoading={isLoading}>
              Save
            </LoaderButton>
          </FormGroup>
        </Col>
      </Row>

      {productId && vendorId === 'hpe' && (
        <Row style={{ textAlign: 'center', marginTop: '20px' }} form>
          <Col lg="12">
            <FormGroup>
              <Button color="falcon-danger" style={{ textAlign: 'center' }} onClick={handleDelete}>
                <FontAwesomeIcon icon={faTrash} /> Delete Managed Product
              </Button>
            </FormGroup>
          </Col>
        </Row>
      )}
    </>
  );
}

ProductActions.propTypes = {
  snProductOptions: PropTypes.array,
  isLoading: PropTypes.bool,
  handleDelete: PropTypes.func,
  handleSave: PropTypes.func,
  handleSaveAndAdd: PropTypes.func,
  vendorId: PropTypes.string,
  productId: PropTypes.string
};
