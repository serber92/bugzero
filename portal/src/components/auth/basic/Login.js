import React, { Fragment } from 'react';
import { Col, Row } from 'reactstrap';
import { Link } from 'react-router-dom';
import LoginForm from '../LoginForm';

const Login = () => (
  <Fragment>
    <Row className="text-left justify-content-between">
      <Col xs="auto" />
    </Row>
    <LoginForm />
  </Fragment>
);

export default Login;
