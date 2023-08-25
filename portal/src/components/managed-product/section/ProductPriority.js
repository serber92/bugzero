import React, { Fragment } from 'react';
import { Card, Col, CardBody, CardText, CardTitle, Row, FormGroup, Label, FormFeedback } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEquals, faMinusCircle } from '@fortawesome/free-solid-svg-icons';
import Select from 'react-select';
import FalconCardHeader from '../../common/FalconCardHeader';
import ButtonIcon from '../../common/ButtonIcon';

// Managed product components
import PropTypes from 'prop-types';

export default function ProductPriority({
  vendorPriorityOptions,
  vendorStatusOptions = [],
  vendorResolutionOptions = [],
  vendorBugCategories = [],
  vendorBugTypes = [],
  setVendorResolutions = [],
  handleSelectChange,
  setVendorStatuses,
  setVendorCategories,
  setVendorTypes,
  vendorStatuses = [],
  vendorCategories = [],
  vendorTypes = [],
  vendorResolutions,
  isSubmitted,
  priorityMaps,
  setPriorityMaps,
  snPriorityOptions,
  title
}) {
  // Prioritiy
  const blankPriority = { vendorPriority: null, snPriority: null };
  const addPriority = () => {
    setPriorityMaps([...priorityMaps, { ...blankPriority }]);
  };
  const removePriority = idx => {
    priorityMaps.splice(idx, 1);
    setPriorityMaps([...priorityMaps]);
  };

  const handleCatChange = (e, idx, field) => {
    const selectedOption = e;
    const updatedPriorities = [...priorityMaps];
    updatedPriorities[idx][field] = selectedOption;
    setPriorityMaps(updatedPriorities);
  };
  return (
    <Card bg={'light'} text={'dark'} style={{}} className="mb-4">
      <FalconCardHeader title={title} />
      <CardBody>
        {!!vendorStatusOptions.length && (
          <>
            <CardTitle>Select Bug Statuses to Monitor</CardTitle>
            <CardText>Select multiple entries if necessary</CardText>
            <Row form>
              <Col lg="5">
                <FormGroup>
                  <Label>
                    Bug Statuses<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select
                    defaultValue={[]}
                    isMulti
                    name="colors"
                    onChange={e => handleSelectChange(e, setVendorStatuses)}
                    value={vendorStatusOptions.filter(vso => {
                      return vendorStatuses.indexOf(vso.value) !== -1;
                    })}
                    options={vendorStatusOptions}
                    className="basic-multi-select"
                    classNamePrefix="select"
                  />
                  <FormFeedback
                    className={isSubmitted && vendorStatusOptions.length && !vendorStatuses.length ? 'd-block' : ''}
                    type="invalid"
                  >
                    Please select a status.
                  </FormFeedback>
                </FormGroup>
              </Col>
            </Row>
            <br />
          </>
        )}
        {!!vendorResolutionOptions.length && (
          <>
            <CardTitle>Select Bug Resolutions to Monitor</CardTitle>
            <CardText>Select multiple entries if necessary</CardText>
            <Row form>
              <Col lg="5">
                <FormGroup>
                  <Label>
                    Bug Resolutions<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select
                    defaultValue={[]}
                    isMulti
                    name="resolutions"
                    onChange={e => handleSelectChange(e, setVendorResolutions)}
                    value={vendorResolutionOptions.filter(vso => {
                      return vendorResolutions.indexOf(vso.value) !== -1;
                    })}
                    options={vendorResolutionOptions}
                    className="basic-multi-select"
                    classNamePrefix="select"
                  />
                  <FormFeedback
                    className={
                      isSubmitted && vendorResolutionOptions.length && !vendorResolutions.length ? 'd-block' : ''
                    }
                    type="invalid"
                  >
                    Please select a resolution.
                  </FormFeedback>
                </FormGroup>
              </Col>
            </Row>
            <br />
          </>
        )}
        {!!vendorBugCategories.length && (
          <>
            <CardTitle>Select Bug Categories to Monitor</CardTitle>
            <CardText>Select multiple entries if necessary</CardText>
            <Row form>
              <Col lg="5">
                <FormGroup>
                  <Label>
                    Bug Categories<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select
                    defaultValue={[]}
                    isMulti
                    name="categories"
                    onChange={e => handleSelectChange(e, setVendorCategories)}
                    value={vendorBugCategories.filter(vso => {
                      return vendorCategories.indexOf(vso.value) !== -1;
                    })}
                    options={vendorBugCategories}
                    className="basic-multi-select"
                    classNamePrefix="select"
                  />
                  <FormFeedback
                    className={isSubmitted && vendorBugCategories.length && !vendorCategories.length ? 'd-block' : ''}
                    type="invalid"
                  >
                    Please select a catetory.
                  </FormFeedback>
                </FormGroup>
              </Col>
            </Row>
            <br />
          </>
        )}
        {!!vendorBugTypes.length && (
          <>
            <CardTitle>Select Bug Type to Monitor</CardTitle>
            <CardText>Select multiple entries if necessary</CardText>
            <Row form>
              <Col lg="5">
                <FormGroup>
                  <Label>
                    Bug Type<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select
                    defaultValue={[]}
                    isMulti
                    name="types"
                    onChange={e => handleSelectChange(e, setVendorTypes)}
                    value={vendorBugTypes.filter(vso => {
                      return vendorTypes.indexOf(vso.value) !== -1;
                    })}
                    options={vendorBugTypes}
                    className="basic-multi-select"
                    classNamePrefix="select"
                  />
                  <FormFeedback
                    className={isSubmitted && vendorBugTypes.length && !vendorBugTypes.length ? 'd-block' : ''}
                    type="invalid"
                  >
                    Please select a type.
                  </FormFeedback>
                </FormGroup>
              </Col>
            </Row>
            <br />
          </>
        )}

        <CardTitle>
          Map Bug Severity to ServiceNow Priority
          <span style={{ color: '#bd472a' }}>*</span>
        </CardTitle>
        <CardText>Specify which severities and priorities to monitor</CardText>
        {!!priorityMaps.length && (
          <Fragment>
            <Row form>
              <Col lg={5}>
                <FormGroup>
                  <Label>Bug Priorities</Label>
                </FormGroup>
              </Col>
              <Col lg={1}>
                <FormGroup style={{ textAlign: 'center', marginTop: '38px' }} />
              </Col>
              <Col lg={5}>
                <FormGroup>
                  <Label>ServiceNow Impact / Urgency / Priority</Label>
                </FormGroup>
              </Col>
            </Row>
          </Fragment>
        )}

        {/* Priority */}
        {priorityMaps.map((val, idx) => {
          const vendorPriority = `vendor-${idx}`;
          const snPriority = `snPriority-${idx}`;
          return (
            <Fragment key={`priority-${idx}`}>
              <Row form>
                <Col md={5}>
                  <FormGroup>
                    <Select
                      id={vendorPriority}
                      name={vendorPriority}
                      value={priorityMaps[idx].vendorPriority}
                      onChange={e => handleCatChange(e, idx, 'vendorPriority')}
                      options={vendorPriorityOptions.filter(vendorPriorityOption => {
                        // Filter out values already set
                        const result = priorityMaps.filter(e => {
                          if (!e.vendorPriority) {
                            return false;
                          }
                          return e.vendorPriority.value === vendorPriorityOption.value;
                        });
                        return result.length ? false : true;
                      })}
                      required
                    />
                    <FormFeedback
                      className={!priorityMaps[idx].vendorPriority && isSubmitted ? 'd-block' : ''}
                      type="invalid"
                    >
                      Please select a priority.
                    </FormFeedback>
                  </FormGroup>
                </Col>
                <Col md={1}>
                  <FormGroup style={{ textAlign: 'center', marginTop: '7px' }}>
                    <FontAwesomeIcon icon={faEquals} />
                  </FormGroup>
                </Col>
                <Col md={5}>
                  <FormGroup>
                    <Select
                      id={snPriority}
                      name={snPriority}
                      value={priorityMaps[idx].snPriority}
                      onChange={e => handleCatChange(e, idx, 'snPriority')}
                      options={snPriorityOptions}
                      required
                    />
                    <FormFeedback
                      className={!priorityMaps[idx].snPriority && isSubmitted ? 'd-block' : ''}
                      type="invalid"
                    >
                      Please select a priority.
                    </FormFeedback>
                  </FormGroup>
                </Col>
                <Col md={1}>
                  <FormGroup style={{ textAlign: 'center', marginTop: '7px' }}>
                    <FontAwesomeIcon icon={faMinusCircle} onClick={() => removePriority(idx)} />
                  </FormGroup>
                </Col>
              </Row>
            </Fragment>
          );
        })}
        <Row form>
          <Col lg="3">
            <FormGroup>
              <FormFeedback className={!priorityMaps.length && isSubmitted ? 'd-block' : ''} type="invalid">
                Please add a priority.
              </FormFeedback>
            </FormGroup>
            <FormGroup>
              <ButtonIcon onClick={addPriority} color="falcon-default" size="sm" icon="plus" iconClassName="fs--2">
                Add priority
              </ButtonIcon>
            </FormGroup>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
}
ProductPriority.defaultProps = {
  vendorStatusOptions: [],
  vendorResolutionOptions: [],
  vendorStatuses: [],
  vendorResolutions: []
};

ProductPriority.propTypes = {
  vendorPriorityOptions: PropTypes.array,
  vendorStatusOptions: PropTypes.array,
  handleSelectChange: PropTypes.func,
  setVendorStatuses: PropTypes.func,
  vendorResolutionOptions: PropTypes.array,
  setVendorResolutions: PropTypes.func,
  vendorResolutions: PropTypes.array,
  vendorStatuses: PropTypes.array,
  isSubmitted: PropTypes.bool,
  priorityMaps: PropTypes.array,
  snPriorityOptions: PropTypes.array,
  setPriorityMaps: PropTypes.func,
  title: PropTypes.string
};
