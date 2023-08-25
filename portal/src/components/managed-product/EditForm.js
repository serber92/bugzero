import React, { useState, useEffect } from 'react';
import { useParams, useHistory } from 'react-router-dom';
import Switch from 'react-switch';
import { toast } from 'react-toastify';
import { Card, CardBody, Row, Col } from 'reactstrap';
// libs
import { onError } from '../../libs/errorLib';
import { validateVendor } from '../../libs/validateLib';

// components
import Loader from '../common/Loader';
// Managed product components
import ProductPriority from './section/ProductPriority';
import ProductActions from './section/ProductActions';
// constants
import vendors from '../../constants/vendors';
import servicenow from '../../constants/servicenow';
// services
import BZAPIService from '../../services/BZAPIService';

export default function ManagedProductForm() {
  const { vendorId, managedProductId: productId } = useParams();
  console.log('productId', productId);
  const history = useHistory();
  // const [managedProduct, setManagedProduct] = useState(null);
  // Set default form values
  const vendor = vendors[vendorId];
  const snPriorityOptions = servicenow.SN_PRIORITY_OPTIONS;
  const vendorPriorityOptions = vendor.priorities;
  const vendorResolutionOptions = vendor.resolutions || [];

  // saving states
  // const [validated, setValidated] = useState('false');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdded, setShowAdded] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);
  const [vendorResolutions, setVendorResolutions] = useState([]);

  // Managed Product
  const [loadedManagedProduct, setLoadedManagedProduct] = useState(null);
  const [snProductId, setSnProductId] = useState(null);
  const [vendorStatuses, setVendorStatuses] = useState([]);

  // Data sources
  // const [vendor, setVendor] = useState({});
  const [vendorProductOptions, setVendorProductOptions] = useState([]);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [priorityMaps, setPriorityMaps] = useState([]);

  useEffect(() => {
    function loadManagedProduct() {
      return BZAPIService.getManagedProduct(productId);
    }

    async function onLoad() {
      try {
        const vendorConfig = await BZAPIService.getSetting(vendorId);

        // Validate config
        console.log('validation', validateVendor(vendorId, vendorConfig));

        console.log('vendorPriorityOptions', vendorPriorityOptions);
        console.log('vendor', vendor);

        const vendorStatusOptions = vendor.statuses || [];

        console.log('vendorStatusOptions', vendorStatusOptions);
        // Set loaded data
        setVendorStatusOptions(vendorStatusOptions);
        setVendorProductOptions(vendorProductOptions);

        // Set Managed product if exists
        const managedProduct = await loadManagedProduct();
        console.log('managedProduct', managedProduct);

        if (managedProduct.vendorData && managedProduct.vendorData.vendorResolutions) {
          setVendorResolutions(managedProduct.vendorData.vendorResolutions);
        }

        console.log('managedProduct.vendorStatuses', managedProduct.vendorStatuses);
        setSnProductId(managedProduct.snProductId);
        setIsDisabled(!!managedProduct.isDisabled);
        setLoadedManagedProduct(managedProduct);
        setVendorStatuses(managedProduct.vendorStatuses);
        // map option values to db values
        const priorityMaps = managedProduct.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
        setPriorityMaps(priorityMaps);
        setIsLoading(false);
      } catch (e) {
        onError(e);
      }
    }

    onLoad();
  }, [productId]);

  function updateManagedProduct() {
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });
    let managedProduct = {
      ...loadedManagedProduct,
      vendorStatuses,
      vendorPriorities,
      vendorData: {
        ...loadedManagedProduct.vendorData,
        vendorResolutions
      },
      vendorId,
      isDisabled
    };

    console.log('managedProduct', managedProduct);

    return BZAPIService.createOrUpdateManagedProduct(managedProduct);
  }

  async function saveProduct() {
    setIsSubmitted(true);
    setIsLoading(true);
    // basic validation

    // Vendor status
    if (vendorStatusOptions.length && !vendorStatuses.length) {
      console.log('Missing vendor status');
      setIsLoading(false);
      return false;
    }

    // Vendor Priority Mapping
    let validPriorities = true;
    priorityMaps.map(item => {
      if (!item.vendorPriority || !item.snPriority) validPriorities = false;
      return item;
    });
    if (!validPriorities) {
      console.log('Invalid priorities');
      setIsLoading(false);
      return false;
    }

    try {
      await updateManagedProduct();
      setIsLoading(false);
      toast.success('Managed product saved!');

      return true;
    } catch (e) {
      onError(e);
      console.error(e);
      setIsLoading(false);
      toast.error('Failed saving product.');

      return false;
    }
  }
  async function handleSave() {
    const result = await saveProduct();
    if (result) history.push(`/vendors/${vendorId}/products`);

    // Go back to listing
  }
  async function handleSaveAndAdd() {
    const result = await saveProduct();
    if (result) {
      setIsSubmitted(false);
      setSnProductId(null);
      setShowAdded(true);
    }
    // Clear Operating system / Product Link
  }

  function deleteManagedProduct() {
    return BZAPIService.deleteManagedProduct(productId);
  }
  // Generic function to handle react-select single/multi-selects
  function handleSelectChange(e, setHook) {
    // if e is null set to empty array for multi-select
    console.log(e, setHook);

    const selected = e || [];
    if (Array.isArray(selected)) setHook(selected.map(el => el.value));
    else setHook(selected.value);
  }
  async function handleToggleEnable() {
    setIsDisabled(!isDisabled);
  }
  async function handleDelete(event) {
    event.preventDefault();

    const confirmed = window.confirm('Are you sure you want to delete this managedProduct?');

    if (!confirmed) {
      return;
    }

    try {
      await deleteManagedProduct();
      history.push(`/managedProducts/${vendorId}`);
    } catch (e) {
      onError(e);
    }
  }
  if (isLoading && !isSubmitted) return <Loader />;
  console.log('snProductId', snProductId);

  return (
    <form noValidate>
      {loadedManagedProduct && (
        <Card className="mb-3">
          <CardBody>
            <Row className="justify-content-between align-items-center">
              <Col md>
                <h5 className="mb-2 mb-md-0">{loadedManagedProduct.name}</h5>
              </Col>
              <Col xs="auto">
                <h5>
                  <span style={{ position: 'relative', top: '3px' }}>
                    <Switch onChange={handleToggleEnable} checked={!isDisabled} height={20} />{' '}
                  </span>

                  <span>{isDisabled ? 'Disabled' : 'Enabled'}</span>
                </h5>
              </Col>
            </Row>
          </CardBody>
        </Card>
      )}
      {/* PRIORITY */}
      <ProductPriority
        title="Bug Configuration"
        vendorPriorityOptions={vendorPriorityOptions}
        vendorResolutionOptions={vendorResolutionOptions}
        vendorStatusOptions={vendorStatusOptions}
        handleSelectChange={handleSelectChange}
        setVendorStatuses={setVendorStatuses}
        vendorStatuses={vendorStatuses}
        setVendorResolutions={setVendorResolutions}
        vendorResolutions={vendorResolutions}
        snProductId={snProductId}
        isSubmitted={isSubmitted}
        priorityMaps={priorityMaps}
        setPriorityMaps={setPriorityMaps}
        snPriorityOptions={snPriorityOptions}
      />
      {/* Form action */}
      <ProductActions
        isLoading={isLoading}
        handleDelete={handleDelete}
        handleSave={handleSave}
        handleSaveAndAdd={handleSaveAndAdd}
        setShowAdded={setShowAdded}
        showAdded={showAdded}
        vendorId={vendorId}
        productId={productId}
      />
    </form>
  );
}
