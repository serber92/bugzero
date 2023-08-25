import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Button, Card, CardBody, CardFooter } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import gethelp from '../../data/faq/gethelp';
import Heading from '../common/Heading';

const QAs = ({ question, answer, divider }) => (
  <Fragment>
    <h6>
      <Link to="#!">
        {question}
        <FontAwesomeIcon icon="caret-right" transform="right-7" />
      </Link>
    </h6>
    <p className="fs--1 mb-0">{answer}</p>
    {divider && <hr className="my-3" />}
  </Fragment>
);

QAs.propTypes = {
  question: PropTypes.string,
  answer: PropTypes.string,
  divider: PropTypes.bool
};

QAs.defaultProps = { divider: true };

const Faq = () => (
  <Fragment>
    <Heading
      title="Support Options"
      subtitle="Below you'll find ways to get support with a BugZero account support specialist"
      className="mb-4 mt-3"
      icon="life-ring"
    />
    <Card>
      <CardBody>
        {gethelp.map((faq, index) => (
          <QAs {...faq} key={index} />
        ))}
      </CardBody>
    </Card>
  </Fragment>
);

export default Faq;
