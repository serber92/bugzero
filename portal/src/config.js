export const version = '2.10.2';
export const navbarBreakPoint = 'xl'; // Vertical navbar breakpoint
export const topNavbarBreakpoint = 'lg';
export const settings = {
  isFluid: false,
  isRTL: false,
  isDark: false,
  isTopNav: false,
  isVertical: true,
  get isCombo() {
    return this.isVertical && this.isTopNav;
  },
  showBurgerMenu: false, // controls showing vertical nav on mobile
  currency: '$',
  isNavbarVerticalCollapsed: false,
  navbarStyle: 'transparent'
};
export default { version, navbarBreakPoint, topNavbarBreakpoint, settings };

const REACT_APP_API_GATEWAY_URL = process.env.REACT_APP_API_GATEWAY_URL;

export const aws = {
  s3: {
    REGION: 'us-east-1'
  },
  apiGateway: {
    REGION: 'us-east-1',
    URL: REACT_APP_API_GATEWAY_URL
  },
  cognito: {
    loginUrl: process.env.REACT_APP_LOGIN_URL
  }
};
