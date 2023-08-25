import React, { useContext } from 'react';
import { Nav } from 'reactstrap';
import ProfileDropdown from './ProfileDropdown';
import NotificationDropdown from './NotificationDropdown';
import AppContext from '../../context/Context';

const TopNavRightSideNavItem = () => {
  const { isTopNav, isCombo } = useContext(AppContext);
  return (
    <Nav navbar className="navbar-nav-icons ml-auto flex-row align-items-center">
      {/* <NotificationDropdown /> */}
      <ProfileDropdown />
    </Nav>
  );
};

export default TopNavRightSideNavItem;
