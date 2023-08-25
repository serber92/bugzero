import React, { useState, useContext } from 'react';
import { Row, Col, Card, CardBody, CustomInput } from 'reactstrap';
import { Line } from 'react-chartjs-2';
import { days, bugsByDays } from '../../data/dashboard/bugs';
import { rgbaColor, themeColors } from '../../helpers/utils';
import AppContext from '../../context/Context';

const ChartTotalBugs = () => {
  const [vendor, setVendor] = useState('all');
  const { isDark } = useContext(AppContext);

  const config = {
    data(canvas) {
      const ctx = canvas.getContext('2d');
      const gradientFill = isDark
        ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
        : ctx.createLinearGradient(0, 0, 0, 250);
      gradientFill.addColorStop(0, isDark ? 'rgba(44,123,229, 0.5)' : 'rgba(255, 255, 255, 0.3)');
      gradientFill.addColorStop(1, isDark ? 'transparent' : 'rgba(255, 255, 255, 0)');

      return {
        labels: days,
        datasets: [
          {
            borderWidth: 2,
            data: bugsByDays[vendor].map(d => (d * 3.14).toFixed(2)),
            borderColor: rgbaColor(isDark ? themeColors.primary : '#fff', 0.8),
            backgroundColor: gradientFill
          }
        ]
      };
    },
    options: {
      legend: { display: false },
      tooltips: {
        mode: 'x-axis',
        xPadding: 20,
        yPadding: 10,
        displayColors: false,
        callbacks: {
          label: tooltipItem => `${days[tooltipItem.index]} - ${tooltipItem.yLabel} bugs`,
          title: () => null
        }
      },
      hover: { mode: 'label' },

      scales: {
        xAxes: [
          {
            scaleLabel: {
              labelString: 'Month'
            },
            ticks: {
              fontColor: rgbaColor('#fff', 0.7),
              fontStyle: 600,
              autoSkip: false
            },
            gridLines: {
              color: rgbaColor('#fff', 0.1),
              zeroLineColor: rgbaColor('#fff', 0.1),
              lineWidth: 1
            }
          }
        ],
        yAxes: [
          {
            display: false,
            gridLines: {
              color: rgbaColor('#fff', 1)
            }
          }
        ]
      }
    }
  };

  return (
    <Card className="mb-3">
      <CardBody className="rounded-soft bg-gradient">
        <Row className="text-white align-items-center no-gutters">
          <Col>
            <h4 className="text-white mb-0">Bugs found this week: 108</h4>
            <p className="fs--1 font-weight-semi-bold">
              Last Week <span className="opacity-50">80</span>
            </p>
          </Col>
          <Col xs="auto" className="d-none d-sm-block">
            <CustomInput
              id="ddd"
              type="select"
              bsSize="sm"
              className="mb-3 shadow"
              value={vendor}
              onChange={({ target }) => setVendor(target.value)}
            >
              <option value="all">All Vendors</option>
              <option value="cisco">Cisco</option>
              <option value="hpe">HPE</option>
              <option value="msft">Microsoft</option>
              <option value="rh">Red Hat</option>
              <option value="vmware">VMware</option>
            </CustomInput>
          </Col>
        </Row>
        <Line data={config.data} options={config.options} width={1618} height={375} />
      </CardBody>
    </Card>
  );
};

export default ChartTotalBugs;
