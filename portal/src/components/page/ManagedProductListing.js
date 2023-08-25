import React, { useState, useEffect, Fragment } from 'react';
import { useParams, Link } from 'react-router-dom';
import { LinkContainer } from 'react-router-bootstrap';
import moment from 'moment';
import { Button, Table, CardBody, Card } from 'reactstrap';
import Switch from 'react-switch';
import FalconCardHeader from '../common/FalconCardHeader';
import ButtonIcon from '../common/ButtonIcon';
import PageHeader from '../common/PageHeader';

import { onError } from '../../libs/errorLib';
import Loader from '../common/Loader';
// import Loading from '../../components/Loading';
import vendorConst from '../../constants/vendors';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';
import BZAPIService from '../../services/BZAPIService';
import { validateVendor } from '../../libs/validateLib';
import Heading from '../common/Heading';
export default function ManagedProductListing() {
  const { vendorId } = useParams();

  const [managedProducts, setManagedProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function onLoad() {
      try {
        const vendorConfig = await BZAPIService.getSetting(vendorId);

        // Validate config
        console.log('validation', validateVendor(vendorId, vendorConfig));

        const managedProducts = await loadManagedProducts();
        console.log('managedProducts', managedProducts);

        setManagedProducts(managedProducts);
      } catch (e) {
        onError(e);
      }

      setIsLoading(false);
    }

    onLoad();
  }, [vendorId]);

  async function handleDelete(managedProduct) {
    const confirmed = window.confirm(`Are you sure you want to delete ${managedProduct.name}?`);

    if (!confirmed || !managedProduct) {
      return;
    }

    // setIsDeleting(true);

    try {
      await BZAPIService.deleteManagedProduct(managedProduct.id);
      const managedProducts = await loadManagedProducts();
      setManagedProducts(managedProducts);
    } catch (e) {
      onError(e);
    }
  }

  async function handleToggleEnable(managedProduct) {
    const confirmed = window.confirm(
      `Are you sure you want to ${managedProduct.isDisabled ? 'enable' : 'disable'} ${managedProduct.name}?`
    );

    if (!confirmed || !managedProduct) {
      return;
    }

    managedProduct.isDisabled = !managedProduct.isDisabled;

    try {
      await BZAPIService.createOrUpdateManagedProduct(managedProduct);
      const managedProducts = await loadManagedProducts();
      setManagedProducts(managedProducts);
    } catch (e) {
      onError(e);
    }
  }
  function loadManagedProducts() {
    return BZAPIService.listManagedProducts(vendorId);
  }

  function renderManagedProductsList(managedProducts) {
    return managedProducts.map(managedProduct => (
      <tr key={managedProduct.id}>
        <td style={{ padding: 0 }}>
          <Link
            style={{
              display: 'inline-block',
              width: '100%',
              height: '100%',
              padding: '1em'
            }}
            key={managedProduct.id}
            to={`/vendors/${vendorId}/products/${managedProduct.id}`}
          >
            {managedProduct.name}
          </Link>
        </td>
        <td>{managedProduct.lastExecution ? moment(managedProduct.lastExecution).fromNow() : 'Pending...'}</td>
        <td>
          <Switch onChange={() => handleToggleEnable(managedProduct)} checked={!managedProduct.isDisabled} />
        </td>
        {vendorId === 'hpe' && (
          <td>
            <Button color="falcon-danger" size="sm" onClick={() => handleDelete(managedProduct)}>
              <FontAwesomeIcon icon={faTimes} className="font-size-sm" />
            </Button>{' '}
          </td>
        )}
      </tr>
    ));
  }
  console.log('vendorConst', vendorConst);
  console.log('vendorId', vendorId);
  return (
    <Fragment>
      <Heading title={vendorConst[vendorId].name} subtitle={`Managed products`} className="mb-4 mt-3" icon="list" />
      <Card>
        {vendorId === 'hpe' && (
          <FalconCardHeader
            title={
              <LinkContainer key="new" to={`/vendors/${vendorId}/products/new`}>
                <ButtonIcon color="falcon-default" size="sm" icon="plus" iconClassName="fs--2">
                  Add managed product
                </ButtonIcon>
              </LinkContainer>
            }
          />
        )}
        <CardBody className="fs--1">
          {isLoading && <Loader />}
          {!isLoading && (
            <>
              {managedProducts.length ? (
                <Table striped bordered hover style={{ marginTop: '20px' }}>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Last Sync</th>
                      <th>Enabled</th>
                      {vendorId === 'hpe' && <th>Remove</th>}
                    </tr>
                  </thead>
                  <tbody>{renderManagedProductsList(managedProducts)}</tbody>
                </Table>
              ) : (
                <div className="text-center">No managed products</div>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </Fragment>
  );
}
