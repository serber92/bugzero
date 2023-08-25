import React, { Fragment, useEffect, useState } from 'react';
import CardSummary from './CardSummary';
import { Row, Col, CardText, CardFooter } from 'reactstrap';
import ServiceWidget from './ServiceWidget';
import Select from 'react-select';

import BZAPIService from '../../services/BZAPIService';
import Heading from '../common/Heading';
import Loader from '../common/Loader';
import VENDORS from '../../constants/vendors';

const Dashboard = () => {
  const bugOptions = [
    { value: 'bugsLastWeek', label: 'Last Week' },
    { value: 'bugsLastMonth', label: 'Last Month' },
    { value: 'bugsLastQuarter', label: 'Last Quarter' }
  ];

  // State
  const [services, setServices] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [bugs, setBugs] = useState({});
  const [priorityStats, setPriorityStats] = useState({});
  const [loadingServices, setLoadingServices] = useState(true);
  const [selectedBugOption, setSelectedBugOption] = useState(bugOptions[0]);

  function buildVendorStat(dataSet, colors) {
    const vendorPriorityStats = {};
    console.log('vendors1', vendors);
    vendors.map(vendor => {
      vendorPriorityStats[vendor.id] = [];
    });

    dataSet.map((bugPriority, id) => {
      if (!vendorPriorityStats[bugPriority.vendorId]) vendorPriorityStats[bugPriority.vendorId] = [];
      const colorIndex = vendorPriorityStats[bugPriority.vendorId].length;
      console.log('color index', colorIndex);
      // const vendorPriority = VENDORS[bugPriority.vendorId].priorities.find(el => {
      //   return (
      //     el.label.toLowerCase() === bugPriority.priority.toLowerCase() ||
      //     el.value.toLowerCase() === bugPriority.priority.toLowerCase() ||
      //     el.bugValue.toLowerCase() === bugPriority.priority.toLowerCase()
      //   );
      // });

      const vendorPriorityStat = {
        id,
        value: bugPriority.priorityCount,
        name: bugPriority.priority,
        color: colors[colorIndex]
      };
      vendorPriorityStats[bugPriority.vendorId].push(vendorPriorityStat);
    });
    console.log('vendorPriorityStatss', vendorPriorityStats);
    // If no data, add 0 data for graph
    Object.keys(vendorPriorityStats).map((key, index) => {
      if (!vendorPriorityStats[key].length) {
        const vendorPriorityStat = {
          id: `z${index}`,
          value: 0.01, // Avoid NaN on graph and don't divide by 0
          name: 'No Bugs',
          color: colors[0]
        };
        vendorPriorityStats[key].push(vendorPriorityStat);
      }
    });
    return vendorPriorityStats;
  }

  useEffect(() => {
    async function onLoad() {
      try {
        const dataPromise = BZAPIService.getDashboard();
        const vendorsPromise = BZAPIService.getVendors();
        const [data, vendorsData] = await Promise.all([dataPromise, vendorsPromise]);
        const { services } = data;
        setServices(services);
        console.log('data', vendorsData);
        console.log('vendorsData', vendorsData);
        const activeVendors = vendorsData.filter(vendor => vendor.active);
        console.log('activeVendors', activeVendors);
        setVendors(activeVendors);
        console.log('vendors', vendors);
        // const bugData = data[selectedBugOption.value];
        setLoadingServices(false);
        // Setup vendor priority stats
        const colors = ['#2c7be5', '#27bcfd', '#d8e2ef', '#2c1be5', '#271cfd', '#d812ef'];
        const bugsLastWeek = buildVendorStat(data.bugsLastWeek, colors);
        const bugsLastMonth = buildVendorStat(data.bugsLastMonth, colors);
        const bugsLastQuarter = buildVendorStat(data.bugsLastQuarter, colors);
        const bugs = {
          bugsLastWeek,
          bugsLastMonth,
          bugsLastQuarter
        };
        console.log('bugs', bugs);
        setPriorityStats(bugsLastWeek);
        setBugs(bugs);
        // Validate config
      } catch (e) {
        console.log(e);
      }
    }

    onLoad();
  }, [loadingServices]);
  async function handleChange(selectedOption) {
    setSelectedBugOption(selectedOption);
    setPriorityStats(bugs[selectedOption.value]);
    console.log(`Option selected:`, selectedOption);
  }
  console.log('selectedBugOption', selectedBugOption);
  // if (loadingServices) return <Loader />;
  return (
    <Fragment>
      <Heading title="Service Status" subtitle={`Current service status`} className="mb-4 mt-3" icon="cog" />
      {loadingServices && <Loader />}
      <div className="card-deck">
        {!loadingServices &&
          services.map(service => {
            let color = 'warning';
            switch (service.status) {
              case 'OPERATIONAL':
                color = 'success';
                break;
              case 'NOT CONFIGURED':
              case 'PENDING':
                color = 'info';
                break;
              case 'ERROR':
                color = 'warning';
                break;
              default:
                break;
            }
            return (
              <CardSummary
                key={service.name}
                title={service.status}
                color={color}
                linkText="View"
                message={service.message}
              >
                {service.name}
              </CardSummary>
            );
          })}
      </div>
      <Heading title="Operational Bugs" subtitle={`Operational bug statistics`} className="mb-4 mt-5" icon="cog" />
      {!loadingServices && (
        <Row noGutters>
          <Col md={6} className="col-xxl-3 mb-3 pr-md-2 pl-xxl-2">
            <Select value={selectedBugOption} onChange={handleChange} options={bugOptions} />
          </Col>
        </Row>
      )}
      {/* <div className="card-deck">{ChartPieExample()}</div> */}
      {loadingServices && <Loader />}

      <Row noGutters>
        {!loadingServices &&
          vendors.length &&
          vendors.map((vendor, key) => {
            console.log('priorityStats', priorityStats);

            return (
              <Col key={key} md={6} className="col-xxl-3 mb-3 pr-md-2 pl-xxl-2">
                <ServiceWidget data={priorityStats[vendor.id] || []} title={vendor.name} />
              </Col>
            );
          })}
      </Row>
      {/* <Row noGutters>
        <Col lg="12" className="pr-lg-2">
          <ActiveUsersBarChart />
        </Col>
      </Row> */}
    </Fragment>
  );
};

export default Dashboard;
