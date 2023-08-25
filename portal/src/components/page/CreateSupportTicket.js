import React, { Fragment, useState } from 'react';
import { useHistory } from 'react-router-dom';
import Select from 'react-select';
import LoaderButton from '../loader-button/LoaderButton';
import { useFormFields } from '../../libs/hooksLib';
import { Button, Card, CardBody, Row, Col, FormGroup, Label, FormFeedback } from 'reactstrap';
import Heading from '../common/Heading';
import TimezoneSelect from 'react-timezone-select';
import BZAPIService from '../../services/BZAPIService';
import { toast } from 'react-toastify';
import { FieldGroup } from '../../libs/formLib';

const CreateSupportTicket = () => {
  const [selectedTimezone, setSelectedTimezone] = useState({});
  const history = useHistory();
  const optionsImpact = [
    { value: 'None', label: 'None' },
    { value: 'Low', label: 'Low' },
    { value: 'Medium', label: 'Medium' },
    { value: 'High', label: 'High' }
  ];
  const optionsHowHelp = [
    { value: 'Something is broken', label: 'Something is broken' },
    { value: 'Performance issue', label: 'Performance issue' },
    { value: 'Outage', label: 'Outage' },
    { value: 'Question', label: 'Question' },
    { value: 'Request', label: 'Request' }
  ];
  const [isValidEmail, setIsValidEmail] = useState(false);
  const [howHelp, setHowHelp] = useState(optionsHowHelp[0]);
  const [impact, setImpact] = useState(optionsImpact[0]);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [fields, handleFieldChange] = useFormFields({
    best_number: '',
    description: '',
    how_can_we_help_you: '',
    impact: '',
    short_description: '',
    steps_to_reproduce: '',
    timezone: '',
    watch_list: ''
  });
  function isEmailListValid(elementValue) {
    //Regex value to validate email
    var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
    // Return true if the value is valid and false if not valid
    return emailPattern.test(elementValue);
  }

  // Generic function to handle react-select single/multi-selects
  function handleSelectChange(e, setHook) {
    // if e is null set to empty array for multi-select
    console.log(e, setHook);

    const selected = e || [];
    if (Array.isArray(selected)) setHook(selected.map(el => el.value));
    else setHook(selected);
  }
  async function handleSave() {
    try {
      let validEmail = false;
      console.log('valid email', isEmailListValid(fields.watch_list));
      // Validate email addresses
      const emailsToTest = fields.watch_list.split(',');
      for (let i = 0; i < emailsToTest.length; i++) {
        const email = emailsToTest[i].trim();
        if (!isEmailListValid(email)) {
          console.log('email', email, 'bad email');
          setIsValidEmail(false);
          validEmail = false;
        } else {
          console.log(email, 'valid email');
          setIsValidEmail(true);
          validEmail = true;
        }
      }

      setIsLoading(true);
      setIsSubmitted(true);
      // Validate
      console.log(fields);
      console.log('selectedTimezone', selectedTimezone);
      if (
        !fields.description ||
        !fields.short_description ||
        !fields.watch_list ||
        !fields.steps_to_reproduce ||
        !validEmail
      ) {
        console.log('error');
        setIsLoading(false);
        return;
      }

      console.log('fields', fields);
      fields.description = `Description: ${fields.description}\n
How can we help: ${howHelp.value}\n
What are the steps to reproduce: \n${fields.steps_to_reproduce}\n
What is the Impact: ${impact.value}\n
Best phone number: ${fields.best_number}\n
Time Zone: ${selectedTimezone.value || ''}\n
			`;
      fields.impact = impact.value;
      fields.how_can_we_help_you = howHelp.value;
      fields.timezone = selectedTimezone.value || '';
      console.log('fields', fields);
      const response = await BZAPIService.createSupportTicket(fields);
      console.log('response', response);
      setIsLoading(false);
      setIsSubmitted(false);

      toast.success(`Support case created successfully!`);
      history.goBack();
    } catch (e) {
      console.log('e', e);
      setIsLoading(false);
      toast.error('An error occurred. Please try again.');
    }
  }

  return (
    <Fragment>
      <Heading
        title="Open a support case"
        subtitle="Fill out the form below to get help from a BugZero support specialist"
        className="mb-4 mt-3"
        icon="life-ring"
      />
      <Card bg={'light'} text={'dak'} className="mb-4">
        <CardBody>
          <Row>
            <Col lg="6">
              <div className="mb-3">
                <FormGroup>
                  <Label>
                    How can we help you?<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select value={howHelp} onChange={e => handleSelectChange(e, setHowHelp)} options={optionsHowHelp} />
                </FormGroup>
              </div>
              <div className="mb-3">
                <FieldGroup
                  type="text"
                  id="watch_list"
                  onChange={handleFieldChange}
                  value={fields.watch_list}
                  label={'Contact email address (separate by comma)'}
                  showFeedback={!isValidEmail && isSubmitted}
                  feedback={'Please specify a valid contact email address.'}
                  placeholder="Enter contact email address"
                  style={{ marginBottom: '10px' }}
                  required
                />
                <FieldGroup
                  type="text"
                  id="short_description"
                  onChange={handleFieldChange}
                  value={fields.short_description}
                  label={'Subject'}
                  showFeedback={!fields.short_description && isSubmitted}
                  feedback={'Please specify a subject.'}
                  placeholder="Enter subject"
                  style={{ marginBottom: '10px' }}
                  required
                />
                <div className="mb-3">
                  <label className="form-label" htmlFor="description">
                    Description<span style={{ color: '#bd472a' }}>*</span>
                  </label>
                  <FormGroup>
                    <textarea onChange={handleFieldChange} className="form-control" id="description" rows="3" />
                  </FormGroup>
                  <FormFeedback className={isSubmitted && !fields.description ? 'd-block' : ''}>
                    Please specify a description the issue.
                  </FormFeedback>
                </div>
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="steps_to_reproduce">
                  What are the steps to reproduce the issue? (Please include the browser you are using)
                  <span style={{ color: '#bd472a' }}>*</span>
                </label>
                <FormGroup>
                  <textarea onChange={handleFieldChange} className="form-control" id="steps_to_reproduce" rows="3" />
                </FormGroup>
                <FormFeedback className={isSubmitted && !fields.steps_to_reproduce ? 'd-block' : ''}>
                  Please specify steps to reproduce the issue.
                </FormFeedback>
              </div>
              <div className="mb-3">
                <FormGroup>
                  <Label>
                    What is the impact?<span style={{ color: '#bd472a' }}>*</span>
                  </Label>
                  <Select value={impact} onChange={e => handleSelectChange(e, setImpact)} options={optionsImpact} />
                </FormGroup>
              </div>
              <div className="mb-3">
                <FieldGroup
                  type="text"
                  id="best_number"
                  onChange={handleFieldChange}
                  value={fields.best_number}
                  label={'If you would like to be contacted by phone number, what is the best number?'}
                  feedback={'Please specify a contact phone number.'}
                  placeholder="1-303-321-4321"
                  style={{ marginBottom: '10px' }}
                />
              </div>
              <div className="	mb-3">
                <label className="form-hlabel" htmlFor="exampleFormControlTextarea3">
                  Please select the timezone you are currently in
                </label>
                <TimezoneSelect value={selectedTimezone} onChange={setSelectedTimezone} />
              </div>
            </Col>
          </Row>
        </CardBody>
      </Card>
      <Row className="flex-between-center">
        <Col xs="auto">
          <Button
            block
            color="falcon-danger"
            onClick={() => {
              history.goBack();
            }}
          >
            Cancel
          </Button>
        </Col>
        <Col xs="auto">
          <LoaderButton block color="falcon-primary" onClick={handleSave} name="save-and-add" isLoading={isLoading}>
            Create support case
          </LoaderButton>
        </Col>
      </Row>
    </Fragment>
  );
};
export default CreateSupportTicket;
